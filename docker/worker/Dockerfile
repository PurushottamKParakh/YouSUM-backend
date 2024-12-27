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

# First copy just requirements to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create start-worker.sh directly in the container
RUN echo '#!/bin/bash\n\
# Wait for Redis\n\
until redis-cli -h redis ping; do\n\
    echo "Waiting for Redis..."\n\
    sleep 1\n\
done\n\
\n\
# Wait for MongoDB\n\
until curl --silent mongodb:27017 > /dev/null; do\n\
    echo "Waiting for MongoDB..."\n\
    sleep 1\n\
done\n\
\n\
# Start the Celery worker\n\
exec celery -A worker.celery_app.celery worker -Q youtube_tasks -l INFO' > /usr/local/bin/start-worker.sh \
    && chmod +x /usr/local/bin/start-worker.sh

# Copy the application code
COPY . .
ENV PYTHONPATH=/app

CMD ["/usr/local/bin/start-worker.sh"]