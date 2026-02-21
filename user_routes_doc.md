# User Routes Documentation

This document lists the routes available in the `app/api/routes/user` directory (and other user-facing routes), including their payload data, return schemas, and full paths.
These routes are mounted on the main `app` instance with specific prefixes.

## 1. Authentication (`authentication.py`) - `/auth`

| Method | Path             | Description        | Payload Data (Body/Query)                                                             | Return Schema                                     |
| :----- | :--------------- | :----------------- | :------------------------------------------------------------------------------------ | :------------------------------------------------ |
| `POST` | `/auth/login`    | User Login.        | **Body**: `{"email": str, "password": str}`                                           | `{"success": bool, "message": str, "token": str}` |
| `POST` | `/auth/register` | User Registration. | **Body**: `{"name": str, "email": str, "password": str, "terms_and_condition": bool}` | `{"success": bool, "message": str, "token": str}` |

## 2. User Management (`user.py`) - `/user`

| Method   | Path             | Description               | Payload Data (Body/Query)                                                           | Return Schema                                           |
| :------- | :--------------- | :------------------------ | :---------------------------------------------------------------------------------- | :------------------------------------------------------ |
| `GET`    | `/user/me`       | Get Current User Details. | **None**                                                                            | `{"user": UserObject, "success": bool}`                 |
| `POST`   | `/user/update`   | Update User Profile.      | **Query**: `name` (opt), `email` (opt), `avatar_id` (opt), `default_model_id` (opt) | `{"success": bool, "user": UserObject, "message": str}` |
| `PUT`    | `/user/password` | Update Password.          | **Query**: `old_password`, `new_password`                                           | `{"success": bool, "data": null, "message": str}`       |
| `DELETE` | `/user/delete`   | Delete Personal Account.  | **Query**: `password`                                                               | `204 No Content`                                        |

## 3. Chat Management (`chat_management.py`) - `/chat`

| Method   | Path                       | Description            | Payload Data (Body/Query)                                       | Return Schema                                                                                             |
| :------- | :------------------------- | :--------------------- | :-------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------- |
| `GET`    | `/chat/list`               | List Chat Sessions.    | **Query**: `limit` (int, default=20), `offset` (int, default=0) | `{"success": bool, "data": [{"id": uuid, "thread_id": uuid, "topic": str, "updated_at": datetime}, ...]}` |
| `DELETE` | `/chat/delete/{thread_id}` | Delete a Chat Session. | **Path**: `thread_id` (uuid)                                    | `{"success": bool, "data": null, "message": str}`                                                         |

## 4. Chat Interaction (`chat_interaction.py`) - `/interaction`

| Method      | Path                                    | Description                    | Payload Data (Body/Query)                                                     | Return Schema                                                                 |
| :---------- | :-------------------------------------- | :----------------------------- | :---------------------------------------------------------------------------- | :---------------------------------------------------------------------------- |
| `WebSocket` | `/interaction/chat`                     | Real-time Chat with Agent.     | **Headers**: `Authorization` (Bearer token), `x-session-thread-id` (optional) | **Text Stream**: Chunks of AI response, followed by `\n✅`                    |
| `GET`       | `/interaction/health/redis-connections` | Check Redis Connection Health. | **None**                                                                      | `{"success": bool, "data": {"active_redis_connections": int, "status": str}}` |

## 5. Tool Authentication (`tool_auth_link.py`) - `/tool-auth`

| Method | Path                        | Description              | Payload Data (Body/Query)                              | Return Schema                              |
| :----- | :-------------------------- | :----------------------- | :----------------------------------------------------- | :----------------------------------------- |
| `POST` | `/tool-auth/tool_auth_link` | Generate Tool Auth Link. | **Body**: `{"platform": str, "state_hash": str (opt)}` | `{"redirect_url": str, "pending_id": str}` |

## 6. Tool Management (`tools_management.py`) - `/tool-management`

| Method   | Path                                                     | Description                          | Payload Data (Body/Query)                                                                                            | Return Schema                                     |
| :------- | :------------------------------------------------------- | :----------------------------------- | :------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------ |
| `POST`   | `/tool-management/tool_auth_callback`                    | Finalize Tool Link (OAuth Callback). | **Body**: `{"platform": str, "installation_id": int, "code": str, "refresh_token": str (opt), "code_verifier": str}` | `{"success": bool, "data": null, "message": str}` |
| `DELETE` | `/tool-management/uninstall_app/{installation_id}`       | Uninstall a Tool/App.                | **Path**: `installation_id` (enc_str)                                                                                | `{"success": bool, "data": null, "message": str}` |
| `PATCH`  | `/tool-management/activate-deactivate/{installation_id}` | Activate or Deactivate a Tool.       | **Path**: `installation_id` (enc_str)<br>**Query**: `is_active` (bool)                                               | `{"success": bool, "data": null, "message": str}` |
