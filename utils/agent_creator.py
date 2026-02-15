from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks.manager import CallbackManager
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from app.agents.cohere_agent import Agents as CohereAgent
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List
import multiprocessing
import asyncio
import logging
import queue
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

num_cores = multiprocessing.cpu_count()
max_workers = num_cores * 6
shared_executor = ThreadPoolExecutor(max_workers=max_workers)


# ── Title Generation (Global Cohere LLM) ──────────────────────────────────────

_title_llm = None

title_prompt = ChatPromptTemplate.from_template("""
Generate a short descriptive title (3-6 words) for this conversation.
Reply with ONLY a JSON object in this exact format, nothing else:
{{"title": "Your Short Title Here"}}

Conversation:
{conversation}
""")


def _get_title_llm():
    """Lazy-load a dedicated Cohere LLM for title generation (singleton)."""
    global _title_llm
    if _title_llm is None:
        _title_llm = CohereAgent().llm_setup(model="command-a-03-2025")
        logger.info("✅ Title generation LLM initialized (command-a-03-2025)")
    return _title_llm


def _extract_title(text: str) -> str | None:
    """Extract title from LLM response, handling markdown code blocks and raw JSON."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    parsed = json.loads(cleaned)
    return parsed.get("title")


async def generate_title(conversation: str) -> str | None:
    """Generate a short topic title from the first conversation exchange.
    Returns None on failure — never disrupts the main chat flow."""
    try:
        formatted = title_prompt.format(conversation=conversation)
        response = await _get_title_llm().ainvoke(formatted)
        title = _extract_title(response.content)
        logger.info(f"🏷️  Generated title: {title}")
        return title
    except Exception as e:
        logger.error(f"❌ Title generation failed: {e}")
        return None
        
class StreamingCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for capturing streaming tokens"""

    def __init__(self):
        self.token_queue = asyncio.Queue()
        self.is_streaming = False
        self.full_content = ""

    def on_llm_start(
        self, serialized, prompts, run_id=None, parent_run_id=None, **kwargs
    ) -> None:
        """Called when LLM starts generating"""
        self.is_streaming = True
        self.full_content = ""
        # Clear any remaining tokens
        while not self.token_queue.empty():
            try:
                self.token_queue.get_nowait()
            except queue.Empty:
                break

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when a new token is generated"""
        if self.is_streaming and token:
            await self.token_queue.put(token)
            self.full_content += token

    async def on_llm_end(self, response, **kwargs: Any) -> None:
        """Called when LLM finishes generating"""
        self.is_streaming = False
        # Signal end of stream
        await self.token_queue.put(None)


class AgentCreator:
    def __init__(
        self, enable_memory: bool, memory_instance=None, tools_list=[], llm=None
    ):
        self.enable_memory = enable_memory
        self.memory_instance = memory_instance
        self.tools_list = tools_list
        self.llm = llm
        self.agent = None
        self.streaming_callback = StreamingCallbackHandler()

    def agent_creator(self):
        if self.agent is not None:
            print("Agent already initialized, returning existing agent.")
            return self.agent

        # Configure LLM for streaming
        if self.llm:
            # Add streaming callback
            if hasattr(self.llm, "callbacks"):
                if self.llm.callbacks is None:
                    self.llm.callbacks = []
                self.llm.callbacks.append(self.streaming_callback)
            elif hasattr(self.llm, "streaming") and hasattr(
                self.llm, "callback_manager"
            ):
                # Enable streaming if supported
                self.llm.streaming = True
                if self.llm.callback_manager is None:
                    self.llm.callback_manager = CallbackManager(
                        [self.streaming_callback]
                    )
                else:
                    self.llm.callback_manager.add_handler(self.streaming_callback)

        if self.enable_memory:
            memory = (
                self.memory_instance
                if self.memory_instance is not None
                else MemorySaver()
            )
            agent = create_react_agent(
                self.llm, tools=self.tools_list, checkpointer=memory
            )
            print("Agent initialized successfully with memory!\n")
            self.agent = agent
            return agent
        else:
            agent = create_react_agent(self.llm, tools=self.tools_list)
            print("Agent initialized successfully!\n")
            self.agent = agent
            return agent

    async def talk_non_stream(self, data: str, thread_id: str) -> str:
        """Fallback non-streaming method (Native Async)"""
        if not self.agent:
            raise RuntimeError("Agent is not set up. Call agent_creator() first.")
        if not thread_id:
            raise ValueError("user id must be provided as thread_id.")

        try:
            config = {"configurable": {"thread_id": thread_id}}
            # Native async call
            result = await self.agent.ainvoke(
                input={"messages": [("human", data)]}, config=config
            )

            # Extract final response
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    return last_message.content
                elif isinstance(last_message, tuple) and len(last_message) > 1:
                    return str(last_message[1])

            return "No response generated."

        except Exception as e:
            logger.error(f"Error in non-streaming talk: {e}")
            return f"Error: {str(e)}"

    async def talk_stream_with_callback(self, data: str, thread_id: str):
        """Stream using callback handler - works if LLM supports streaming callbacks"""
        if not self.agent:
            raise RuntimeError("Agent is not set up. Call agent_creator() first.")
        if not thread_id:
            raise ValueError("user id must be provided as thread_id.")

        try:
            # Reset callback handler
            self.streaming_callback.token_queue = asyncio.Queue()
            self.streaming_callback.full_content = ""

            # Start agent in background task (non-blocking)
            async def run_agent_async():
                config = {"configurable": {"thread_id": thread_id}}
                await self.agent.ainvoke(
                    input={"messages": [("human", data)]}, config=config
                )

            # Fire and forget (the callback will feed the queue)
            agent_task = asyncio.create_task(run_agent_async())

            # Stream tokens as they come
            tokens_yielded = 0
            while True:
                try:
                    # Check if agent is done
                    if agent_task.done():
                        # Check for exceptions in the task
                        exc = agent_task.exception()
                        if exc:
                            raise exc
                        
                        # Get any remaining tokens
                        while True:
                            try:
                                token = self.streaming_callback.token_queue.get_nowait()
                                if token is None:  # End marker
                                    break
                                yield token
                                tokens_yielded += 1
                            except queue.Empty:
                                break
                        break

                    # Get token with timeout
                    try:
                        token = await asyncio.wait_for(self.streaming_callback.token_queue.get(), timeout=0.05)
                        if token is None:  # End marker
                            break
                        yield token
                        tokens_yielded += 1
                    except asyncio.TimeoutError:
                        # No token yet, continue waiting
                        continue

                except Exception as e:
                    logger.error(f"Error getting token: {e}")
                    break

            # Wait for agent to complete (structure already ensures done, but good practice)
            await agent_task

            # If no tokens were streamed, fall back to full response
            if tokens_yielded == 0:
                result = agent_task.result()
                # If ainvoke returns "None" or similar (it shouldn't if configured right), handle it
                if result and "messages" in result and result["messages"]:
                    last_message = result["messages"][-1]
                    if hasattr(last_message, "content"):
                        content = last_message.content
                        for char in content:
                            yield char
                            await asyncio.sleep(0.01)

        except Exception as e:
            error_msg = (
                f"Error during callback streaming: {type(e).__name__} - {str(e)}"
            )
            logger.error(error_msg)
            # Re-raise to let the caller handle it (e.g. stop retrying)
            raise e

    async def talk_stream(self, data: str, thread_id: str):
        """
        Main streaming method - tries different approaches in order of preference
        """
        logger.info(f"Starting streaming for thread {thread_id}")

        # Method 1: Try callback-based streaming (works with some LLMs)
        try:
            logger.info("Attempting callback-based streaming...")
            token_count = 0
            async for token in self.talk_stream_with_callback(data, thread_id):
                # We expect clean strings here. If exceptions occur in generator, they should be raised.
                token_count += 1
                yield token

            # Callback streaming completed successfully
            logger.info(f"Callback streaming completed with {token_count} tokens")
            return

        except Exception as e:
            logger.error(f"Callback streaming failed: {e}")
            yield f"Error: {str(e)}"
            return
