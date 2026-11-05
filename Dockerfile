FROM python:3.12-slim

ENV ASTAR_HOST=0.0.0.0 \
    PORT=8080 \
    ASTAR_DATA_DIR=/data \
    ASTAR_LEARNING_ONLY=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY astar_app ./astar_app
COPY static/learn ./static/learn

RUN mkdir -p /data
EXPOSE 8080
VOLUME ["/data"]

CMD ["python", "-m", "astar_app.server"]
