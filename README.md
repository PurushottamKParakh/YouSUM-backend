# YouSUM Backend
## Backend Set-up

```bash
cd YouSUM-backend
cp .env.example .env
# then update .env file with your OPEN API Key
# then just run
docker-compose up -d
```
## High-Level Architecture
The backend processes YouTube video summarizations and transcripts using a **microservices-like architecture** consisting of the following components:

1. **API Service**:
   - Built with **Flask**.
   - Exposes RESTful APIs for handling video summarization and transcript requests.
   - Implements **rate-limiting** using Redis.

2. **Task Queue**:
   - Uses **Celery** for asynchronous task processing.
   - Tasks include fetching video transcripts and generating summaries.

3. **Database**:
   - **MongoDB** stores:
     - Video summaries.
     - Transcripts.
     - Metadata for efficient querying.
   - Indexes are created for fast lookups on video ID and settings.

4. **Caching**:
   - **Redis** is used:
     - For rate-limiting (via `flask-limiter`).
     - As the message broker for Celery.

5. **Worker Service**:
   - Processes background tasks.
   - Interacts with third-party APIs (e.g., OpenAI for summarization).

6. **Health Monitoring**:
   - Provides health-check endpoints for Redis and MongoDB.

---

## Component Breakdown

### 1. **API Service**
- **Endpoints**:
  - `/api/transcript`: Fetches transcripts from YouTube videos.
  - `/api/summarize`: Requests video summarizations.
  - `/api/result`: Retrieves processed summaries.
  - `/api/redis-health`: Checks Redis health.
  - `/api/redis-debug`: Debugs Redis tasks.
- **Features**:
  - Rate-limiting using `flask-limiter`.
  - Input validation (e.g., URL and language validation).
  - Caching for transcripts and summaries to avoid redundant processing.

### 2. **Worker Service**
- **Task Execution**:
  - Asynchronous tasks are executed via Celery.
  - Tasks include:
    - Fetching YouTube video transcripts.
    - Summarizing video content using OpenAI APIs.

- **Startup Script** (`start-worker.sh`):
  - Ensures Redis and MongoDB are available before starting the worker.
  - Starts the Celery worker process.

### 3. **MongoDB**
- **Collections**:
  - `summaries`: Stores video summaries with queryable metadata (e.g., video ID, length, focus areas).
  - `transcripts`: Stores transcripts indexed by video ID and language.
- **Indexes**:
  - Optimized for querying summaries and transcripts based on video ID, language, and settings.
- **Functions**:
  - `save_to_db`: Saves a summary.
  - `get_from_db`: Retrieves a summary.
  - `save_transcript_to_db`: Saves a transcript.
  - `get_transcript_from_db`: Retrieves a transcript.

### 4. **Redis**
- Used for:
  - **Rate-limiting** API requests.
  - **Message brokering** for Celery.
- Health checks ensure Redis availability.

### 5. **Dockerized Deployment**
- **docker-compose.yaml**:
  - Defines services for `api`, `worker`, `redis`, and `mongodb`.
  - Ensures service dependencies (`depends_on`) for Redis and MongoDB.
  - Includes health checks for Redis and MongoDB.

- **Dockerfile** (for API and Worker):
  - Uses a Python base image.
  - Installs dependencies (`requirements.txt`).
  - Copies application code.

---

## System Workflow

### 1. **Transcript Retrieval Workflow**
- API receives a request for a transcript (`/api/transcript`).
- Validates the YouTube URL.
- Checks MongoDB for cached transcript.
  - **Cache hit**: Returns transcript from MongoDB.
  - **Cache miss**: Adds task to Celery queue.
- Celery worker fetches the transcript and stores it in MongoDB.

### 2. **Video Summarization Workflow**
- API receives a request for summarization (`/api/summarize`).
- Validates URL and settings (length, focus areas, language).
- Checks MongoDB for cached summary.
  - **Cache hit**: Returns summary from MongoDB.
  - **Cache miss**: Adds task to Celery queue.
- Celery worker processes the task:
  - Fetches the transcript if not already available.
  - Calls OpenAI API to generate a summary.
  - Stores the summary in MongoDB.

---

## Scalability Considerations
1. **API Scaling**:
   - Use load balancers to scale API horizontally.
   - Use Redis clustering for rate-limiting across multiple API instances.

2. **Worker Scaling**:
   - Deploy multiple Celery workers to process tasks in parallel.
   - Use task routing to distribute workloads.

3. **Database Scaling**:
   - Shard MongoDB for large datasets.
   - Optimize indexes for frequent queries.

4. **Caching**:
   - Add an in-memory caching layer (e.g., Redis with TTL) for frequently accessed data.

---

## Error Handling and Fault Tolerance
1. **Worker Retry Logic**:
   - Celery retries failed tasks with exponential backoff.
2. **Health Checks**:
   - Ensure API and worker services are healthy via `/redis-health` and `/redis-debug`.
3. **Graceful Failures**:
   - Return meaningful error messages for invalid inputs or service unavailability.
---

## Monitoring

1. **Check the logs**:
   ```bash
   docker-compose logs worker
   ```

2. **Monitor Redis queues**:
   ```bash
   docker exec -it youtube-summarizer-dockerized-backend-redis-1 redis-cli
   ```
   Then within Redis CLI:
   ```bash
   KEYS *
   ```

3. **Check MongoDB for stored summaries**:
   ```bash
   docker exec -it youtube-summarizer-dockerized-backend-mongodb-1 mongosh
   ```
   Then within MongoDB shell:
   ```bash
   use youtube_summary
   db.summaries.find()
---

## Future Improvements
1. **Streaming Processing**:
   - Process live video streams in real-time, which will provide summary of earlier played part of the video.
2. **Analytics**:
   - Track API usage and task performance for monitoring.
3. **Maintaining History for each user**:
   - Once integrated with login module, we can easily maintain history for each user.
4. **Optimizing for Performance**:
   - Use Redis for caching as currently we are directly fetching from mongo db.
5. **Login Authentication**: 
   - Implement login authentication along with Google login/Facebook login/Apple login
6. **Edges cases**:
   - **Batching Short Videos**: Aggregate multiple short videos into a single batch for summarization through one API call. This approach is straightforward, leveraging batch size limits that are tuned beforehand.
   - **Segmenting Long Videos**: Divide long videos into multiple segments, process each segment separately through different API calls for summarization, and merge the results seamlessly.
   

