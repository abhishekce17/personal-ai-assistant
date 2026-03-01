# 1. Multi-stage build: get redis-stack binaries from the official ubuntu/debian image
FROM redis/redis-stack-server:latest AS redis-stack

# 2. Start with a newer, fully-patched Python 3.12 SLIM base image to save ~800MB
FROM python:3.12-slim-bookworm

# 3. Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 4. Upgrade system packages and install necessary system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    git \
    supervisor \
    libpq-dev \
    gcc \
    python3-dev \
    libgomp1 \
    procps \
    zstd \
    && rm -rf /var/lib/apt/lists/*

# 5. Extract only the necessary Redis Stack Modules & Server
COPY --from=redis-stack /opt/redis-stack/bin/redis-server /usr/local/bin/redis-stack-server
COPY --from=redis-stack /opt/redis-stack/lib/ /opt/redis-stack/lib/

# 6. Install Ollama manually and immediately delete the 4.6GB GPU runners
RUN curl -L https://ollama.com/download/ollama-linux-amd64.tar.zst -o ollama.tar.zst \
    && tar -C /usr -xf ollama.tar.zst \
    && rm ollama.tar.zst \
    && rm -rf /usr/lib/ollama/cuda_* /usr/lib/ollama/mlx_cuda_* /usr/lib/ollama/vulkan

# 7. Set working directory
WORKDIR /app

# 8. Install Python dependencies using uv AND clean the cache to save ~440MB
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv pip install --system -r pyproject.toml && uv cache clean

# 9. Copy your application code
COPY . .

# 10. Set up Hugging Face non-root user (id 1000) EARLY so we can pull models as this user
RUN useradd -m -u 1000 user

# 11. Create necessary directories and set permissions
RUN mkdir -p /var/log/supervisor /var/run/supervisor /var/lib/redis /app/.ollama/models
RUN chown -R user:user /app /var/log/supervisor /var/run/supervisor /var/lib/redis /app/.ollama
ENV OLLAMA_MODELS=/app/.ollama/models

# 12. Switch to non-root user before pulling the model
USER user

# 13. Pre-pull the embedding model during the build phase (owned by correct user)
ENV OLLAMA_HOST=127.0.0.1
RUN nohup bash -c "ollama serve &" && \
    sleep 5 && \
    ollama pull nomic-embed-text && \
    pkill ollama

# 14. Configure Supervisord to run all three services using the 1-line chown command
COPY --chown=user:user supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 15. Expose the default Hugging Face port
EXPOSE 7860

# 16. Set environment variables that FastAPI needs
ENV LOCAL_REDIS_URL="redis://localhost:6379"

# 17. Start Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]