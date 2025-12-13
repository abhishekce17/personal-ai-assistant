# Admin Routes Documentation

This document lists all the routes available in the `app/api/routes/admin` directory, including their return schemas and full paths.
The base path for all admin routes is `/admin`.

## 1. Authentication (`authentication.py`) - `/admin/auth`

| Method | Path | Description | Return Schema |
| :--- | :--- | :--- | :--- |
| `POST` | `/admin/auth/login` | Admin login. Returns an access token. | `{"message": str, "accessToken": str}` |
| `POST` | `/admin/auth/register` | Register a new admin. | `{"message": str, "token": str}` |

## 2. Plan & Model/Tool Mapping (`model_feature_tools_plan_mapping.py`) - `/admin/model-feature-tools-plan-mapping`

| Method | Path | Description | Return Schema |
| :--- | :--- | :--- | :--- |
| `POST` | `/admin/model-feature-tools-plan-mapping/plan-model` | Map a model to a plan. | `{"message": str, "mapping_id": str}` |
| `GET` | `/admin/model-feature-tools-plan-mapping/plan-model` | List all Plan-Model mappings. | `{"count": int, "mappings": [{"mapping_id": str, "plan_id": str, "plan_name": str, "model_id": str, "model_name": str, "created_at": datetime, "updated_at": datetime, "is_active": bool}, ...]}` |
| `DELETE` | `/admin/model-feature-tools-plan-mapping/plan-model/{mapping_id}` | Delete a Plan-Model mapping by ID. | `{"message": str, "mapping_id": str}` |
| `PATCH` | `/admin/model-feature-tools-plan-mapping/plan-model/{mapping_id}` | Activate or Deactivate a Plan-Model mapping by ID. | `{"success": bool, "message": str}` |
| `POST` | `/admin/model-feature-tools-plan-mapping/plan-tool` | Map a tool to a plan. | `{"message": str, "mapping_id": str}` |
| `GET` | `/admin/model-feature-tools-plan-mapping/plan-tool` | List all Plan-Tool mappings. | `{"count": int, "mappings": [{"mapping_id": str, "plan_id": str, "plan_name": str, "tool_id": str, "tool_name": str, "created_at": datetime, "updated_at": datetime, "is_active": bool}, ...]}` |
| `DELETE` | `/admin/model-feature-tools-plan-mapping/plan-tool/{mapping_id}` | Delete a Plan-Tool mapping by ID. | `{"message": str, "mapping_id": str}` |
| `PATCH` | `/admin/model-feature-tools-plan-mapping/plan-tool/{mapping_id}` | Activate or Deactivate a Plan-Tool mapping by ID. | `{"success": bool, "message": str}` |

## 3. Model Management (`model_management.py`) - `/admin/model`

*Full Model Object*: `id`, `created_at`, `updated_at`, `is_active`, `model_name`, `model_description`, `model_provider`, `tool_support`, `user_count`, `model_image`, `is_default`

| Method | Path | Description | Return Schema |
| :--- | :--- | :--- | :--- |
| `POST` | `/admin/model/create` | Create a new AI model. | `{"message": str, "model": {"id": str, "name": str}}` |
| `PUT` | `/admin/model/update/{model_id}` | Update an existing AI model. | `{"message": str, "model": {"id": str, "name": str}}` |
| `GET` | `/admin/model/list` | List all AI models. | `[ModelObject, ...]` |
| `DELETE` | `/admin/model/delete/{model_id}` | Delete an AI model. | `{"message": str}` |
| `PATCH` | `/admin/model/activate-deactivate/{model_id}` | Activate or Deactivate a model by ID. | `{"success": bool, "message": str}` |

## 4. Plan Management (`plan_management.py`) - `/admin/plan`

*Full Plan Object*: `id`, `created_at`, `updated_at`, `is_active`, `name`, `slug`, `subscription_count`, `price`, `description`, `is_default`

| Method | Path | Description | Return Schema |
| :--- | :--- | :--- | :--- |
| `POST` | `/admin/plan/create` | Create a new plan. | `{"message": str, "plan": {"id": str, "name": str}}` |
| `GET` | `/admin/plan/list` | List all plans. | `[PlanObject, ...]` |
| `DELETE` | `/admin/plan/delete/{plan_id}` | Delete a plan. | `{"message": str}` |
| `PUT` | `/admin/plan/update/{plan_id}` | Update an existing plan. | `{"message": str, "plan": {"id": str, "name": str, "price": int, "description": str}}` |
| `PATCH` | `/admin/plan/activate-deactivate/{plan_id}` | Activate or Deactivate a plan by ID. | `{"success": bool, "message": str}` |

## 5. Static Data Management (`staticdata_management.py`) - `/admin/staticdata-management`

*Full SystemArtifact Object*: `id`, `created_at`, `updated_at`, `is_active`, `reference_key`, `revision_id`, `artifact_payload`, `media_type`, `description`

| Method | Path | Description | Return Schema |
| :--- | :--- | :--- | :--- |
| `POST` | `/admin/staticdata-management/create` | Create a new static artifact. | `{"message": str, "static_data": {"id": str, "reference_key": str}}` |
| `GET` | `/admin/staticdata-management/list` | List all static artifacts. | `[SystemArtifactObject, ...]` |
| `DELETE` | `/admin/staticdata-management/delete/{artifact_id}` | Delete a static artifact. | `{"message": str}` |
| `PUT` | `/admin/staticdata-management/update/{artifact_id}` | Update an existing static artifact. | `{"message": str, "static_data": {"id": str, "reference_key": str, "revision_id": int}}` |
| `PATCH` | `/admin/staticdata-management/activate-deactivate/{artifact_id}` | Activate or Deactivate a static artifact. | `{"success": bool, "message": str}` |

## 6. Tool Management (`tool_management.py`) - `/admin/tool-management`

*Full Tool Object*: `id`, `created_at`, `updated_at`, `is_active`, `tool_name`, `tool_description`, `tool_provider`, `user_count`, `tool_image`

| Method | Path | Description | Return Schema |
| :--- | :--- | :--- | :--- |
| `POST` | `/admin/tool-management/create` | Create a new tool. | `{"message": str, "tool": {"id": str, "name": str}}` |
| `GET` | `/admin/tool-management/list` | List all tools. | `[ToolObject, ...]` |
| `DELETE` | `/admin/tool-management/delete/{tool_id}` | Delete a tool. | `{"message": str}` |
| `PUT` | `/admin/tool-management/update/{tool_id}` | Update an existing tool. | `{"message": str, "tool": {"id": str, "name": str, "provider": str, "description": str, "image": str}}` |
| `PATCH` | `/admin/tool-management/activate-deactivate/{tool_id}` | Activate or Deactivate a tool by ID. | `{"success": bool, "message": str}` |

## 7. User Management (`user_management.py`) - `/admin/user-management`

| Method | Path | Description | Return Schema |
| :--- | :--- | :--- | :--- |
| `GET` | `/admin/user-management/users` | List all users. | `[{"avatar": str, "name": str, "email": str, "id": str, "created_at": datetime, "current_plan_id": str, "is_active": bool, "plan_name": str, "slug": str}, ...]` |
| `POST` | `/admin/user-management/users/{id}` | Get user details by ID. | `{"user_*": UserField, "plan_*": PlanField}` (Combined User and Plan fields) |
| `PATCH` | `/admin/user-management/users/{id}/activate` | Activate or Deactivate a user by ID. | `{"success": bool, "message": str}` |
| `POST` | `/admin/user-management/users/{id}/plan/{plan_id}` | Change user plan by ID. | `{"success": bool, "message": str}` |
