# docker/worker/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Add MongoDB's official repository
RUN apt-get update && apt-get install -y wget gnupg \
    && wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | apt-key add - \
    && echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/debian buster/mongodb-org/4.4 main" | tee /etc/apt/sources.list.d/mongodb-org-4.4.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        redis-tools \
        mongodb-database-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH=/app

COPY docker/worker/start-worker.sh /start-worker.sh
RUN chmod +x /start-worker.sh

CMD ["/start-worker.sh"]