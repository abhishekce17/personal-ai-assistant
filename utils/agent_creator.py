from langchain.callbacks.base import BaseCallbackHandler
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List
import multiprocessing
import traceback
import asyncio
import logging
import redis
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


num_cores = multiprocessing.cpu_count()  # Should be 12 for your CPU
max_workers = num_cores * 6  # 72 threads, safe for mixed I/O and CPU

shared_executor = ThreadPoolExecutor(max_workers=max_workers)


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
                    from langchain.callbacks.manager import CallbackManager

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
        """Fallback non-streaming method (Runs sync invoke in a thread)"""
        if not self.agent:
            raise RuntimeError("Agent is not set up. Call agent_creator() first.")
        if not thread_id:
            raise ValueError("user id must be provided as thread_id.")

        try:
            # Define synchronous worker function
            def _run_invokation():
                config = {"configurable": {"thread_id": thread_id}}
                return self.agent.invoke(
                    input={"messages": [("human", data)]}, config=config
                )

            # Offload to thread pool to avoid blocking event loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(shared_executor, _run_invokation)

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

            # Run agent in thread
            def run_agent():
                config = {"configurable": {"thread_id": thread_id}}
                return self.agent.invoke(
                    input={"messages": [("human", data)]}, config=config
                )

            # Start agent in background thread
            loop = asyncio.get_running_loop()
            agent_task = loop.run_in_executor(shared_executor, run_agent)

            # Stream tokens as they come
            tokens_yielded = 0
            while True:
                try:
                    # Check if agent is done
                    if agent_task.done():
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
                        token = await self.streaming_callback.token_queue.get()
                        if token is None:  # End marker
                            break
                        yield token
                        tokens_yielded += 1
                    except queue.Empty:
                        # No token yet, continue waiting
                        await asyncio.sleep(0.05)
                        continue

                except Exception as e:
                    logger.error(f"Error getting token: {e}")
                    break

            # Wait for agent to complete
            await agent_task

            # If no tokens were streamed, fall back to full response
            if tokens_yielded == 0:
                result = agent_task.result()
                if "messages" in result and result["messages"]:
                    last_message = result["messages"][-1]
                    if hasattr(last_message, "content"):
                        content = last_message.content
                        for char in content:
                            yield char
                            await asyncio.sleep(0.03)

        except Exception as e:
            error_msg = (
                f"❌ Error during callback streaming: {type(e).__name__} - {str(e)}"
            )
            logger.error(error_msg)
            logger.error(f"Full traceback:\n{traceback.format_exc()}")
            yield error_msg

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
                if not token.startswith("❌"):
                    token_count += 1
                    yield token
                    if token_count >= 5:  # If we get several tokens, this method works
                        continue
                else:
                    # Error in callback method, try next approach
                    logger.info("Callback streaming failed, trying word-by-word...")
                    break
            else:
                # Callback streaming completed successfully
                logger.info(f"Callback streaming completed with {token_count} tokens")
                return

        except Exception as e:
            logger.info(f"Callback streaming failed: {e}")
