#!/bin/sh

# Limit the allowed LLMs to a predefined set
ALLOWED_MODELS="\
  llama3.2:3b \
  llama3.1:8b \
  codellama:7b \
  codellama:13b \
  mistral:7b \
  codestral:22b \
  deepseek-r1:14b \
  qwen3:14b \
  qwen2.5-coder:3b \
  qwen2.5-coder:7b \
  qwen2.5-coder:14b\
  deepseek-coder:6.7b \
  granite3.3:8b
"

# Require OLLAMA_MODEL env variable
if [ -z "$OLLAMA_MODEL" ]; then
  echo "ERROR: OLLAMA_MODEL environment variable is not set. Please specify a model from the allowed list: $ALLOWED_MODELS" >&2
  exit 1
fi

MODEL="$OLLAMA_MODEL"

# Check if model is allowed
if ! echo "$ALLOWED_MODELS" | grep -wq "$MODEL"; then
  echo "ERROR: Model '$MODEL' is not in the list of allowed models: $ALLOWED_MODELS" >&2
  exit 1
fi

# Start Ollama in background
ollama serve &

# Wait until server is healthy
echo "⏳ Waiting for Ollama to be ready..."
while true; do
  if curl -s http://localhost:11434 > /dev/null; then
    break
  fi
  sleep 1
done

# Pull the model
echo "⬇️ Pulling model $MODEL..."
ollama pull "$MODEL"

# Prevent container from exiting
tail -f /dev/null
