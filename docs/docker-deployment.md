# LightRAG-Core Docker Deployment

This directory contains Docker configuration for deploying LightRAG-Core.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start all services (LightRAG-Core + Ollama)
docker-compose up -d

# View logs
docker-compose logs -f lightrag-core

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Using Docker directly

```bash
# Build image
docker build -t lightrag-core:latest .

# Run with external Ollama
docker run -d \
  -p 8000:8000 \
  -e LIGHTRAG_LLM_BASE_URL=http://host.docker.internal:11434 \
  -v lightrag-data:/app/data \
  lightrag-core:latest
```

## Configuration

### Environment Variables

All configuration can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LIGHTRAG_LLM_PROVIDER` | `ollama` | LLM provider: `ollama` or `deepseek` |
| `LIGHTRAG_LLM_MODEL` | `llama3` | Model name |
| `LIGHTRAG_LLM_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `LIGHTRAG_LLM_API_KEY` | `""` | API key (for DeepSeek) |
| `LIGHTRAG_LLM_TEMPERATURE` | `0.7` | Generation temperature |
| `LIGHTRAG_LLM_MAX_TOKENS` | `1024` | Max tokens |
| `LIGHTRAG_LLM_TOP_P` | `0.9` | Top-p sampling |
| `LIGHTRAG_LLM_TIMEOUT` | `120` | Request timeout (seconds) |
| `LIGHTRAG_EMBEDDING_MODEL` | `BAAI/bge-m3` | Embedding model name |
| `LIGHTRAG_VECTOR_STORE_TYPE` | `faiss` | Vector store: `faiss` or `qdrant` |
| `LIGHTRAG_RERANKER_ENABLED` | `true` | Enable/disable reranker (`true` / `false`) |
| `LIGHTRAG_DB_PATH` | `lightrag.db` | SQLite database path |
| `LIGHTRAG_DEBUG` | `false` | Debug mode |

### Using External Ollama

If you have Ollama running on the host machine, update `docker-compose.yml`:

```yaml
environment:
  - LIGHTRAG_LLM_BASE_URL=http://host.docker.internal:11434
```

Then remove the `depends_on` and `ollama` service.

### Using External Vector Store (Qdrant)

```yaml
environment:
  - LIGHTRAG_VECTOR_STORE_TYPE=qdrant
```

## Volumes

| Volume | Path | Purpose |
|--------|------|---------|
| `lightrag-data` | `/app/data` | SQLite database and FAISS index persistence |
| `ollama-data` | `/root/.ollama` | Ollama models |

## Health Check

The container exposes a health check endpoint at `/health`:

```bash
curl http://localhost:8000/health
```

## Production Considerations

1. **Security**: The container runs as non-root user (`appuser`)
2. **Persistence**: Data is stored in Docker volumes for persistence across restarts
3. **Scaling**: For production, consider using an external vector store (Qdrant) and database
4. **SSL/TLS**: Use a reverse proxy (nginx, traefik) for HTTPS termination
5. **Monitoring**: Health check endpoint is available for container orchestrators

## Troubleshooting

### Container fails to start

Check logs:
```bash
docker-compose logs lightrag-core
```

### Ollama connection refused

Ensure Ollama is accessible from the container:
```bash
# Test from inside container
docker exec -it lightrag-core curl http://ollama:11434/api/tags
```

### Models not downloaded

If using the built-in Ollama service, models need to be pulled manually or uncomment the `entrypoint` in `docker-compose.yml`.

## Build Arguments

None currently supported. To customize the build, modify the `Dockerfile`.
