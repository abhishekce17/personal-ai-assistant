# User Routes Documentation

This document lists the routes available in the `app/api/routes/user` directory (and other user-facing routes), including their payload data, return schemas, and full paths.
These routes are mounted on the main `app` instance with specific prefixes.

## 1. Authentication (`authentication.py`) - `/auth`

| Method | Path             | Description        | Payload Data (Body/Query)                                                             | Return Schema                                     |
| :----- | :--------------- | :----------------- | :------------------------------------------------------------------------------------ | :------------------------------------------------ |
| `POST` | `/auth/login`    | User Login.        | **Body**: `{"email": str, "password": str}`                                           | `{"success": bool, "message": str, "token": str}` |
| `POST` | `/auth/register` | User Registration. | **Body**: `{"name": str, "email": str, "password": str, "terms_and_condition": bool}` | `{"success": bool, "message": str, "token": str}` |

## 2. User Management (`user.py`) - `/user`

| Method   | Path             | Description               | Payload Data (Body/Query)                                 | Return Schema                                           |
| :------- | :--------------- | :------------------------ | :-------------------------------------------------------- | :------------------------------------------------------ |
| `GET`    | `/user/me`       | Get Current User Details. | **None**                                                  | `{"user": UserObject, "success": bool}`                 |
| `POST`   | `/user/update`   | Update User Profile.      | **Query**: `name` (opt), `email` (opt), `avatar_id` (opt) | `{"success": bool, "user": UserObject, "message": str}` |
| `PUT`    | `/user/password` | Update Password.          | **Query**: `old_password`, `new_password`                 | `{"success": bool, "data": null, "message": str}`       |
| `DELETE` | `/user/delete`   | Delete Personal Account.  | **Query**: `password`                                     | `204 No Content`                                        |

## 3. Static Data (`staticdata.py`) - `/staticdata`

| Method | Path                | Description                               | Payload Data (Body/Query)                                        | Return Schema                                                                                |
| :----- | :------------------ | :---------------------------------------- | :--------------------------------------------------------------- | :------------------------------------------------------------------------------------------- |
| `POST` | `/staticdata/fetch` | Fetch System Artifacts by reference keys. | **Body**: `{"reference_keys": ["terms", "privacy_policy", ...]}` | `{"success": bool, "data": {"terms": {artifact_obj}, "privacy_policy": {}}, "message": str}` |

## 4. Feature Flag (`feature_flag.py`) - `/feature-flag`

| Method | Path                   | Description                     | Payload Data (Body/Query) | Return Schema                                                                   |
| :----- | :--------------------- | :------------------------------ | :------------------------ | :------------------------------------------------------------------------------ |
| `GET`  | `/feature-flag/active` | Fetch all active feature flags. | **None**                  | `{"success": bool, "data": {"new_ui": {flag_obj}, "beta": {}}, "message": str}` |

## 5. Chat Management (`chat_management.py`) - `/chat`

| Method   | Path                        | Description                                                   | Payload Data (Body/Query)                                                                       | Return Schema                                                                                                                                   |
| :------- | :-------------------------- | :------------------------------------------------------------ | :---------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------- |
| `GET`    | `/chat/list`                | List/Search Chat Sessions.                                    | **Query**: `search` (str, opt), `limit` (int, default=10), `offset` (int, default=0)            | `{"success": bool, "data": [{"id": uuid, "thread_id": uuid, "topic": str, "pinned": datetime, "updated_at": datetime}, ...], "has_more": bool}` |
| `PATCH`  | `/chat/pin/{thread_id}`     | Toggle Pin status.                                            | **Path**: `thread_id` (uuid)<br>**Query**: `pin` (bool)                                         | `{"success": bool, "data": {"pinned": datetime}, "message": str}`                                                                               |
| `GET`    | `/chat/history/{thread_id}` | Get Paginated Thread History.                                 | **Path**: `thread_id` (uuid)<br>**Query**: `limit` (int, default=20), `offset` (int, default=0) | `{"success": bool, "data": {"id": uuid, "thread_id": uuid, "topic": str, "messages": [...]}, "pagination": {...}}`                              |
| `DELETE` | `/chat/delete/{thread_id}`  | Completely Delete a Chat Session (PostgreSQL, Redis, Qdrant). | **Path**: `thread_id` (uuid)                                                                    | `{"success": bool, "data": null, "message": str}`                                                                                               |

## 4. Chat Interaction (`chat_interaction.py`) - `/interaction`

| Method      | Path                                    | Description                    | Payload Data (Body/Query)                                                     | Return Schema                                                                                                                                                                                                                                                                                                       |
| :---------- | :-------------------------------------- | :----------------------------- | :---------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `WebSocket` | `/interaction/chat`                     | Real-time Chat with Agent.     | **Headers**: `Authorization` (Bearer token), `x-session-thread-id` (optional) | **Handshake Header**: `x-session-thread-id`<br>**Text Stream** of AI chunks, then **JSON events**:<br>`{"event":"reasoning"}`<br>`{"event":"turn_complete", "thread_id": uuid, "status": str}`<br>`{"event":"topic_generated", "id": uuid, "topic": str, "thread_id": uuid}`<br>`{"event":"error", "message": str}` |
| `GET`       | `/interaction/health/redis-connections` | Check Redis Connection Health. | **None**                                                                      | `{"success": bool, "data": {"active_redis_connections": int, "status": str}}`                                                                                                                                                                                                                                       |

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
