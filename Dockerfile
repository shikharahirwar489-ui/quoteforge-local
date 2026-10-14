FROM python:3.12-alpine
WORKDIR /app
COPY server.py .
COPY static ./static
ENV APP_HOST=0.0.0.0 APP_PORT=8000 OLLAMA_HOST=http://ollama:11434 OLLAMA_MODEL=llama3.2
EXPOSE 8000
CMD ["python", "server.py"]
