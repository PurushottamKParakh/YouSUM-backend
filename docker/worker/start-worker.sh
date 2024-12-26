#!/bin/bash

# Wait for Redis
until redis-cli -h redis ping; do
    echo "Waiting for Redis..."
    sleep 1
done

# Wait for MongoDB
until curl --silent mongodb:27017 > /dev/null; do
    echo "Waiting for MongoDB..."
    sleep 1
done

# Start the Celery worker
exec celery -A worker.celery_app.celery worker -Q youtube_tasks -l INFO