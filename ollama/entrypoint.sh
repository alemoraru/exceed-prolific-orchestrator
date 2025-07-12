#!/bin/sh

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
echo "⬇️ Pulling model llama3.1:8b..."
ollama pull llama3.1:8b

# Prevent container from exiting
tail -f /dev/null
