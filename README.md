---
title: Orvio HF Backend
emoji: 🚀
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# Orvio HF Backend (Personal AI Assistant)

This repository contains the backend service for **Orvio**, a personal AI assistant. It is designed to be fully self-contained, running a high-performance **FastAPI** server alongside **Redis Stack** and a local **Ollama** embedding model. Everything is bundled inside a single Docker container managed by **Supervisord**, making it fully optimized for deployments on platforms like Hugging Face Spaces.

## 🌟 Key Features

*   **FastAPI & WebSockets:** Provides high-speed RESTful APIs for administrative tasks and real-time WebSocket communication for seamless chat experiences with users.
*   **Local AI Embeddings:** Integrates **Ollama** directly within the container to generate embeddings securely and privately, removing the need for external API dependencies for vector embeddings.
*   **Advanced Caching & Vector Database:** Utilizes **Redis Stack** for ultra-fast vector similarity search (RAG), conversational state management, and API request caching.
*   **Self-Contained Deployment:** Uses **Supervisord** as a process manager to orchestrate FastAPI, Redis, and Ollama simultaneously within a single Docker container.
*   **Role-Based Access & Routing:** Segregated API structures for regular end-users (`/user`) and secure administrative endpoints (`/admin`).

## 🛠️ Tech Stack

*   **Framework:** FastAPI (Python)
*   **Database / Cache:** Redis Stack (Vector DB / Caching / Storage)
*   **AI / ML Engine:** Ollama (Local Embedding Models)
*   **Containerization:** Docker, Supervisord
*   **Package Management:** `uv` (Fast Python package installer)

## 🚀 Quick Start (Running Locally)

To test or run this backend locally, ensure you have [Docker](https://www.docker.com/) installed on your machine.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/abhishekce17/personal-ai-assistant.git
   cd personal-ai-assistant
   ```

2. **Build and start the container:**
   ```bash
   docker build -t orvio-backend .
   docker run -p 8000:8000 orvio-backend
   ```
   *Note: This spins up the FastAPI server, Redis database, and the Ollama model simultaneously using Supervisord.*

3. **Access the API Documentation:**
   Once running, FastAPI automatically generates interactive API documentation. You can view and test the endpoints directly from your browser:
   * **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
   * **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## 🏗️ Backend Architecture

The following diagram illustrates the internal flow of data and how the different services interact within the single Hugging Face Docker container.

```mermaid
graph TD
    %% Define Styles (Added color:#000; to force black text on light backgrounds)
    classDef client fill:#f9f9f9,stroke:#333,stroke-width:2px,color:#000;
    classDef docker fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,stroke-dasharray: 5 5,color:#000;
    classDef api fill:#c8e6c9,stroke:#388e3c,stroke-width:2px,color:#000;
    classDef db fill:#ffcc80,stroke:#f57c00,stroke-width:2px,color:#000;
    classDef ai fill:#d1c4e9,stroke:#512da8,stroke-width:2px,color:#000;

    %% External Clients
    Client_User["📱 User Client"]:::client
    Client_Admin["💻 Admin Client"]:::client

    %% Docker Container Wrapper
    subgraph Docker_Container ["🐳 Single Docker Container(HuggingFace Space)"]
        
        %% API Layer
        FastAPI_Server["⚡ FastAPI Server<br/>(server.py)"]:::api
        Router_User["🛣️ User Routes<br/>(user_routes_doc.md)"]:::api
        Router_Admin["🛣️ Admin Routes<br/>(admin_routes_doc.md)"]:::api
        
        %% Processing Layer
        App_Logic["⚙️ App & Business Logic<br/>(/app & /utils)"]:::api
        
        %% Internal Services
        Redis["🗄️ Redis Stack<br/>(Vector DB / Caching / Storage)"]:::db
        Ollama["🧠 Ollama<br/>(Embedding Model)"]:::ai
        Supervisor["🛠️ Supervisord<br/>(Process Manager)"]:::docker
        
        %% Internal API Connections
        FastAPI_Server --> Router_User
        FastAPI_Server --> Router_Admin
        
        Router_User --> App_Logic
        Router_Admin --> App_Logic
        
        App_Logic <-->|"Read/Write Data & Vectors"| Redis
        App_Logic <-->|"Generate Embeddings"| Ollama
        
        %% Supervisor manages processes
        Supervisor -.->|"Manages"| FastAPI_Server
        Supervisor -.->|"Manages"| Redis
        Supervisor -.->|"Manages"| Ollama
    end

    %% External Connections
    Client_User <-->|"REST / WebSockets"| Router_User
    Client_Admin <-->|"REST APIs"| Router_Admin
```