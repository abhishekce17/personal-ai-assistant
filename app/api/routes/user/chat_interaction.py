# routes/chat_interaction.py - Fixed WebSocket Handler with Proper Streaming
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException
from langgraph.checkpoint.redis import RedisSaver
from utils.agent_creator import AgentCreator
from db.models import Model, User, PlanModel
from app.core.security import verify_jwt_token
from app.core.config import RedisCheckpoint
from main import SocketAgentLLM
from utils.types import ConversationType
import importlib
import json
from dotenv import load_dotenv
from db.db import get_db_session
from typing import Dict
import threading
import logging
import uuid
import os

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

redis_saver = RedisCheckpoint.get_saver()

convo_type: ConversationType = ConversationType.NON_STREAM

enabled_tools = ["github"]  # Moking for now, can be dynamic based on user plan


class UserAgentManager:
    _user_agents: Dict[str, SocketAgentLLM] = {}
    _lock = threading.Lock()

    @classmethod
    def get_user_llm(cls, id: str, model_name: str) -> SocketAgentLLM:
        with cls._lock:
            if id not in cls._user_agents:
                logger.info(
                    f"Creating new SocketAgentLLM with Redis connection for user: {id}"
                )

                socket_llm = SocketAgentLLM()

                try:
                    socket_llm.setup(model_name=model_name)
                    cls._user_agents[id] = socket_llm
                    logger.info(
                        f"✅ Successfully created Redis connection for users: {cls._user_agents.keys()}"
                    )

                except Exception as e:
                    logger.error(
                        f"❌ Failed to create llm connection for user {cls._user_agents.keys()}: {e}"
                    )
                    try:
                        socket_llm.cleanup()
                    except:
                        pass
                    raise
            else:
                logger.info(f"♻️ Reusing existing llm connection for user: {id}")

            return cls._user_agents[id]

    @classmethod
    def remove_user_llm(cls, id: str):
        with cls._lock:
            if id in cls._user_agents:
                try:
                    logger.info(f"🔄 Cleaning up llm connection for user: {id}")
                    cls._user_agents[id].cleanup()
                    del cls._user_agents[id]
                    logger.info(
                        f"✅ Successfully cleaned up llm connection for user: {id}"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Error cleaning up llm connection for user {id}: {e}"
                    )
                    if id in cls._user_agents:
                        del cls._user_agents[id]

    @classmethod
    def cleanup_all(cls):
        with cls._lock:
            user_ids = list(cls._user_agents.keys())
            logger.info(f"🧹 Cleaning up {len(user_ids)} llm connections")

            for id in user_ids:
                try:
                    cls._user_agents[id].cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up agent for user {id}: {e}")

            cls._user_agents.clear()
            logger.info("✅ All llm connections cleaned up")

    @classmethod
    def get_active_connections_count(cls):
        with cls._lock:
            return len(cls._user_agents)


@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    id = None
    socket_agent = None
    db = None

    try:
        # Authentication
        token = websocket.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            logger.warning("No token provided")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        try:
            payload = verify_jwt_token(token)
            id = payload.get("id")

            if not id:
                logger.warning("No id in token")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            try:
                authorized_plan_model = None
                async with get_db_session() as db:
                    # Get user and model information
                    user = (
                        db.query(User.default_model_id, User.current_plan_id)
                        .filter((User.id == id) & (User.is_active == True))
                        .first()
                    )
                    if not user:
                        logger.warning(f"User not found: {id}")
                        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                        return

                    default_model_id = user.default_model_id
                    current_plan_id = user.current_plan_id

                    authorized_plan_model = (
                        db.query(Model.model_name)
                        .join(PlanModel, PlanModel.model_id == Model.id)
                        .filter(
                            (PlanModel.model_id == default_model_id)
                            & (PlanModel.plan_id == current_plan_id)
                            & (PlanModel.is_active == True)
                        )
                        .scalar()
                    )

                if not authorized_plan_model:
                    logger.warning(f"Unauthorized model for user: {id}")
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return

                logger.info(f"WebSocket connection established for user: {id}")
                socket_llm = UserAgentManager.get_user_llm(
                    id, model_name=authorized_plan_model
                )
                model = socket_llm.get_model_name()

                await websocket.send_text(f"Connected as {id} using {model}")

                thread_id = uuid.uuid4()

                tools = []
                try:
                    for tool in enabled_tools:
                        #this external token should be hashed/encrypted in production
                        x_external_tokens = json.loads(
                            websocket.headers.get("X-External-Tool-Tokens", "")
                        )
                        if tool + "_access_token" in x_external_tokens:
                            tool_module = importlib.import_module(
                                f"app.Tools.{tool}_tools"
                            )
                            if tool_module and hasattr(tool_module, "make_tools"):
                                tools += tool_module.make_tools(
                                    PAT=x_external_tokens[tool + "_access_token"]
                                )

                except Exception as e:
                    logger.error(f"Error loading tools for user {id}: {e}")

                socket_agent = AgentCreator(
                    enable_memory=True,
                    memory_instance=redis_saver,
                    llm=socket_llm.llm,
                    tools_list=tools,
                )
                socket_agent.agent_creator()

                # Main chat loop with improved streaming
                while True:
                    try:
                        data = await websocket.receive_text()
                        logger.info(f"Received message from {id}: {data[:100]}...")

                        # Send typing indicator
                        await websocket.send_text("Thinking...")

                        # Stream the response
                        response_started = False
                        full_response = ""

                        if convo_type == ConversationType.STREAM:
                            try:
                                async for chunk in socket_agent.talk_stream(
                                    data, thread_id=str(thread_id)
                                ):
                                    if chunk:
                                        if not response_started:
                                            await websocket.send_text(f"\r{model}: ")
                                            response_started = True

                                        await websocket.send_text(chunk)
                                        full_response += chunk

                            except Exception as streaming_error:
                                logger.error(
                                    f"Streaming error for user {id}: {streaming_error}"
                                )
                                await websocket.send_text(
                                    f"\n❌ Streaming error: {str(streaming_error)}"
                                )
                        else:
                            # Fallback to non-streaming response
                            try:
                                fallback_response = socket_agent.talk_non_stream(
                                    data, str(thread_id)
                                )
                                await websocket.send_text(
                                    f"\n{model} (fallback): {fallback_response}"
                                )
                            except Exception as fallback_error:
                                logger.error(
                                    f"Fallback error for user {id}: {fallback_error}"
                                )
                                await websocket.send_text(
                                    f"\n❌ Error: {str(fallback_error)}"
                                )

                        # Send end-of-response marker
                        if response_started:
                            await websocket.send_text("\n✅")
                            logger.info(
                                f"Completed response for {id} ({len(full_response)} chars)"
                            )

                    except WebSocketDisconnect:
                        logger.info(f"🔌 Client {id} disconnected")
                        break
                    except Exception as e:
                        logger.error(f"❌ Error processing message for {id}: {e}")
                        await websocket.send_text(f"❌ Error: {str(e)}")

            finally:
                if RedisCheckpoint._redis_saver:
                    RedisCheckpoint.close_connection()
                logger.debug(f"[DB] Session closed for WebSocket user: {id}")

        except HTTPException as e:
            logger.warning(f"Authentication failed: {e.detail}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)

        except Exception as e:
            logger.error(f"Unexpected error during setup: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)

    except WebSocketDisconnect:
        logger.info("Client disconnected before authentication")

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        if id:
            if RedisCheckpoint._redis_saver:
                RedisCheckpoint.close_connection()
            logger.info(f"🧹 Cleaning up Redis connection for disconnected user: {id}")
            UserAgentManager.remove_user_llm(id)
            remaining_connections = UserAgentManager.get_active_connections_count()
            logger.info(
                f"📊 Remaining active Redis connections: {remaining_connections}"
            )


@router.get("/health/redis-connections")
async def get_redis_connections_status():
    active_connections = UserAgentManager.get_active_connections_count()
    return {
        "active_redis_connections": active_connections,
        "status": ("healthy" if active_connections < 50 else "warning"),
    }
