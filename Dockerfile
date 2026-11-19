FROM python:3.12-slim
WORKDIR /app
COPY mvp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && useradd -m appuser
COPY mvp /app/mvp
RUN mkdir -p /app/runtime/mvp && chown -R appuser:appuser /app
USER appuser
EXPOSE 8080
CMD ["sh", "-c", "uvicorn mvp.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
