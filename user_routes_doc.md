# User Routes Documentation

This document lists the routes available in the `app/api/routes/user` directory (and other user-facing routes), including their payload data, return schemas, and full paths.
These routes are mounted directly on the main `app` instance.

## 1. Tool Authentication (`tool_auth_link.py`) - `/tool-auth-link`

| Method | Path | Description | Payload Data (Body/Query) | Return Schema |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/tool-auth-link/tool_auth_link` | Generate Tool Auth Link. | **Body**: `{"platform": str, "state_hash": str (opt)}` | `{"redirect_url": str, "pending_id": str}` |
| `POST` | `/tool-auth-link/tool_auth_callback` | Finalize Tool Link. | **Body**: `{"platform": str, "installation_id": int, "state_id": str, "code": str, "refresh_token": str, "code_verifier": str}` | `{"status": str, "message": str}` |
