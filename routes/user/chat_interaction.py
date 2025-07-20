# routes/chat_interaction.py - Fixed WebSocket Handler
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, HTTPException
from utils.security import verify_jwt_token
from db.models import Model, User, PlanModel
from db.db import DBEngine
import logging
import threading
from typing import Dict
from main import SocketAgent

router = APIRouter()
logger = logging.getLogger(__name__)


class UserAgentManager:
    _user_agents: Dict[str, SocketAgent] = {}
    _lock = threading.Lock()

    @classmethod
    def get_user_agent(cls, id: str, model_name: str) -> SocketAgent:
        with cls._lock:
            if id not in cls._user_agents:
                logger.info(
                    f"Creating new SocketAgent with Redis connection for user: {id}"
                )

                socket_agent = SocketAgent()

                try:
                    socket_agent.setup(model_name=model_name)
                    cls._user_agents[id] = socket_agent
                    logger.info(
                        f"✅ Successfully created Redis connection for users: {cls._user_agents.keys()}"
                    )

                except Exception as e:
                    logger.error(
                        f"❌ Failed to create Redis connection for user {cls._user_agents.keys()}: {e}"
                    )
                    try:
                        socket_agent.cleanup()
                    except:
                        pass
                    raise
            else:
                logger.info(f"♻️ Reusing existing Redis connection for user: {id}")

            return cls._user_agents[id]

    @classmethod
    def remove_user_agent(cls, id: str):
        with cls._lock:
            if id in cls._user_agents:
                try:
                    logger.info(f"🔄 Cleaning up Redis connection for user: {id}")
                    cls._user_agents[id].cleanup()
                    del cls._user_agents[id]
                    logger.info(
                        f"✅ Successfully cleaned up Redis connection for user: {id}"
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Error cleaning up Redis connection for user {id}: {e}"
                    )
                    if id in cls._user_agents:
                        del cls._user_agents[id]

    @classmethod
    def cleanup_all(cls):
        with cls._lock:
            user_ids = list(cls._user_agents.keys())
            logger.info(f"🧹 Cleaning up {len(user_ids)} Redis connections")

            for id in user_ids:
                try:
                    cls._user_agents[id].cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up agent for user {id}: {e}")

            cls._user_agents.clear()
            logger.info("✅ All Redis connections cleaned up")

    @classmethod
    def get_active_connections_count(cls):
        with cls._lock:
            return len(cls._user_agents)


@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    id = None
    socket_agent = None
    db = None  # Define early for cleanup

    try:
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

            db = DBEngine().SessionLocal()

            try:
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
                socket_agent = UserAgentManager.get_user_agent(
                    id, model_name=authorized_plan_model
                )
                model = socket_agent.get_model_name()

                await websocket.send_text(f"Connected as {id} using {model}")

                thread_id = uuid.uuid4()
                # while True:
                #     try:
                #         data = await websocket.receive_text()
                #         response = socket_agent.talk(data, thread_id=str(thread_id))

                #         if "messages" in response and response["messages"]:
                #             last_message = response["messages"][-1]
                #             if (
                #                 isinstance(last_message, tuple)
                #                 and last_message[0] == "ai"
                #             ):
                #                 await websocket.send_text(f"{model}: {last_message[1]}")
                #             elif hasattr(last_message, "content"):
                #                 await websocket.send_text(
                #                     f"{model}: {last_message.content}"
                #                 )
                #             else:
                #                 await websocket.send_text(
                #                     f"{model}: No response generated."
                #                 )
                #         else:
                #             await websocket.send_text(
                #                 f"{model}: No response generated."
                #             )

                #     except WebSocketDisconnect:
                #         logger.info(f"🔌 Client {id} disconnected")
                #         break
                #     except Exception as e:
                #         logger.error(f"❌ Error processing message for {id}: {e}")
                #         await websocket.send_text(f"Error: {str(e)}")

                while True:
                    try:
                        data = await websocket.receive_text()
                        async for chunk in socket_agent.talk_stream(
                            data, thread_id=str(thread_id)
                        ):
                            await websocket.send_text(f"{model}: {chunk}")

                    except WebSocketDisconnect:
                        logger.info(f"🔌 Client {id} disconnected")
                        break
                    except Exception as e:
                        logger.error(f"❌ Error processing message for {id}: {e}")
                        await websocket.send_text(f"Error: {str(e)}")

            finally:
                db.close()
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
            logger.info(f"🧹 Cleaning up Redis connection for disconnected user: {id}")
            UserAgentManager.remove_user_agent(id)
            remaining_connections = UserAgentManager.get_active_connections_count()
            logger.info(
                f"📊 Remaining active Redis connections: {remaining_connections}"
            )


@router.get("/health/redis-connections")
async def get_redis_connections_status():
    active_connections = UserAgentManager.get_active_connections_count()
    return {
        "active_redis_connections": active_connections,
        "status": (
            "healthy" if active_connections < 50 else "warning"
        ),  # Adjust threshold as needed
    }
