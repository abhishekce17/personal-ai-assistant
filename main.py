from utils.llm_models import OpenRouter_Agents, Ollama_LLM, Cohere_Agents
from Agents.open_router_agents import Agents as OpenRouterAgent
from Agents.cohere_agent import Agents as CohereAgent
from Agents.local_ollama_llm_agents import Agents
from langgraph.checkpoint.redis import RedisSaver
from dotenv import load_dotenv
import traceback
import logging
import os

load_dotenv()


# def main():
#     """Main chat loop for the LangChain PDF chat application."""
#     print("Type 'exit', 'quit', or 'q' to stop the conversation.\n")

#     try:
#         # agent_instance = CohereAgent()
#         # open_router_agent_instance = OpenRouterAgent()
#         agent_instance = Agents()
#         # agent = agent_instance.mistral_agent()
#         # agent = agent_instance.mistral_agent()

#         # agent = open_router_agent_instance.open_router_agent(
#         #     model=OpenRouter_Agents.DEEPSEEK_V3.value, enable_memory=True
#         # )

#         redis_uri = os.getenv("REDIS_URL")
#         print("Using Redis at:", redis_uri)

#         with RedisSaver.from_conn_string(redis_uri) as checkpointer:
#             checkpointer.setup()
#             # agent = agent_instance.cohere_agent(
#             #     enable_memory=True, memory_instance=checkpointer
#             # )

#             agent = agent_instance.local_ollama_agent(
#                 memory_instance=checkpointer,
#                 model=Ollama_LLM.LLAMA3_1.value,
#                 enable_memory=True,
#             )

#             config = {"configurable": {"thread_id": "user123"}}

#             while True:
#                 try:
#                     user_input = input("User: ").strip()

#                     if not user_input:
#                         print("Please enter a message.\n")
#                         continue

#                     if user_input.lower() in ["exit", "quit", "q"]:
#                         print("Goodbye!")
#                         break

#                     # Use ("human", ...) format for message input
#                     result = agent.invoke(
#                         input={"messages": [("human", user_input)]}, config=config
#                     )

#                     # Read final assistant response
#                     if "messages" in result and result["messages"]:
#                         last_message = result["messages"][-1]
#                         if isinstance(last_message, tuple) and last_message[0] == "ai":
#                             print(f"Assistant: {last_message[1]}\n")
#                         elif hasattr(last_message, "content"):
#                             print(f"Assistant: {last_message.content}\n")
#                         else:
#                             print("Assistant: No response generated.\n")
#                     else:
#                         print("Assistant: No response generated.\n")
#                 except KeyboardInterrupt:
#                     print("\nConversation interrupted. Goodbye!")
#                     break
#     except Exception as e:
#         print(f"Error initializing agent: {e}")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()

logger = logging.getLogger(__name__)


class SocketAgent:
    __checkpointer = None  # shared RedisSaver

    def __init__(self):
        self.agent = None
        self._model_name = None
        self._is_setup = False

    def setup(self, model_name: str):
        if self._is_setup:
            return self._model_name

        try:
            cls = type(self)
            if cls.__checkpointer is None:
                with RedisSaver.from_conn_string(
                    os.getenv("LOCAL_REDIS_URL")
                ) as redis_saver:
                    redis_saver.setup()
                    cls.__checkpointer = redis_saver

            if model_name in Cohere_Agents._value2member_map_:
                agent_instance = CohereAgent()
            elif model_name in OpenRouter_Agents._value2member_map_:
                agent_instance = OpenRouterAgent()
            # only for local testing while development with local llm
            elif model_name in Ollama_LLM._value2member_map_:
                agent_instance = Agents()
            else:
                raise ValueError(f"Unsupported model: {model_name}")

            logger.info("model selected successfully, now initializing agent...")

            self.agent = agent_instance.create_agent(
                memory_instance=cls.__checkpointer,
                model=model_name,
                enable_memory=True,
            )

            self._model_name = agent_instance.get_model()
            self._is_setup = True
            return self._model_name

        except Exception as e:
            self.cleanup()
            raise (f"Failed to setup agent with model {model_name}: {e}")

    async def talk_stream(self, data: str, thread_id: str):
        if not self._is_setup or not self.agent:
            raise RuntimeError("Agent is not set up. Call setup() first.")
        if not thread_id:
            raise ValueError("user id must be provided as thread_id.")

        try:
            config = {"configurable": {"thread_id": thread_id}}
            stream = self.agent.astream(
                input={"messages": [("human", data)]},
                config=config,
            )
            logger.info(f"Stream object: {stream}")

            async for chunk in stream:
                logger.info(f"Chunk: {repr(chunk)}")
                try:
                    if isinstance(chunk, dict) and "content" in chunk:
                        yield chunk["content"]
                    elif hasattr(chunk, "content"):
                        yield chunk.content
                    else:
                        yield str(chunk)
                except Exception as inner_e:
                    logger.error(
                        f"❌ Error while processing chunk: {inner_e}", exc_info=True
                    )
                    yield f"[CHUNK ERROR]: {str(inner_e)}"

        except Exception as e:
            logger.error(f"❌ Error during agent stream:\n{traceback.format_exc()}")
            yield f"[STREAM ERROR]: {type(e).__name__} - {str(e)}"

    def cleanup(self):
        """Cleans only this agent, NOT the shared Redis connection"""
        self.agent = None
        self._model_name = None
        self._is_setup = False

    def get_model_name(self):
        """Returns the model name if set, otherwise raises an error."""
        if not self._model_name:
            raise RuntimeError("Model name is not set. Call setup() first.")
        return self._model_name

    @classmethod
    def cleanup_shared_redis(cls):
        """Closes the shared Redis connection once"""
        if cls.__checkpointer:
            try:
                cls.__checkpointer.delete_thread()
                cls.__checkpointer.close()
                logger.info("✅ Shared Redis connection closed")
            except Exception as e:
                logger.error(f"❌ Failed to close Redis connection: {e}")
            finally:
                cls.__checkpointer = None
