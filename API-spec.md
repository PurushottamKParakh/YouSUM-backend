# API Specification for YouSUM Backend

## Base URL
All API endpoints are hosted under the following base URL:
```
http://<backend-domain>:5000/api
```
Replace `<backend-domain>` with the actual domain or IP address of the backend server.

---

## **1. Fetch Video Transcript**
### Endpoint
```
GET /transcript
```
### Description
Retrieves the transcript of a YouTube video in the specified language.

### Request
#### Query Parameters:
| Field      | Type   | Description                           |
|------------|--------|---------------------------------------|
| `url`      | string | The URL of the YouTube video.         |
| `language` | string | Language code (e.g., `en`, `es`, etc.). Defaults to `en`. |

### Response
#### Success (200):
```json
{
  "status": "completed",
  "video_id": "string",
  "transcript": "string"
}
```
| Field          | Type   | Description                     |
|----------------|--------|---------------------------------|
| `status`       | string | Task status, always `completed`. |
| `video_id`     | string | The ID of the YouTube video.    |
| `transcript`   | string | The retrieved transcript.       |

#### Failure (400/500):
```json
{
  "status": "error",
  "message": "string"
}
```
| Field      | Type   | Description              |
|------------|--------|--------------------------|
| `status`   | string | Task status, always `error`. |
| `message`  | string | Error message.            |

---

## **2. Generate Video Summary**
### Endpoint
```
GET /summarize
```
### Description
Generates a summary for the given YouTube video based on user-defined settings.

### Request
#### Query Parameters:
| Field            | Type       | Description                               |
|------------------|------------|-------------------------------------------|
| `url`            | string     | The URL of the YouTube video.             |
| `length`         | string     | Summary length (`short`, `medium`, `long`). Defaults to `medium`. |
| `focus_areas`    | array      | Areas to focus on (e.g., `key_points`, `technical_details`). |
| `language`       | string     | Language code (e.g., `en`, `es`). Defaults to `en`. |

### Response
#### Success (200):
```json
{
  "status": "completed",
  "video_id": "string",
  "summary": "string"
}
```
| Field          | Type   | Description                     |
|----------------|--------|---------------------------------|
| `status`       | string | Task status, always `completed`. |
| `video_id`     | string | The ID of the YouTube video.    |
| `summary`      | string | The generated summary.          |

#### Failure (400/500):
```json
{
  "status": "error",
  "message": "string"
}
```
| Field      | Type   | Description              |
|------------|--------|--------------------------|
| `status`   | string | Task status, always `error`. |
| `message`  | string | Error message.            |

---

## **3. Check Redis Health**
### Endpoint
```
GET /redis-health
```
### Description
Checks the health of the Redis service used for rate-limiting and task queuing.

### Response
#### Success (200):
```json
{
  "status": "ok",
  "message": "Redis is healthy."
}
```
| Field      | Type   | Description                 |
|------------|--------|-----------------------------|
| `status`   | string | Always `ok`.                |
| `message`  | string | Health status of Redis.     |

#### Failure (500):
```json
{
  "status": "error",
  "message": "string"
}
```
| Field      | Type   | Description                 |
|------------|--------|-----------------------------|
| `status`   | string | Always `error`.             |
| `message`  | string | Error message.              |

---

## **4. Debug Redis**
### Endpoint
```
GET /redis-debug
```
### Description
Provides debug information for the Redis queues.

### Response
#### Success (200):
```json
{
  "status": "ok",
  "queues": [
    {
      "queue": "string",
      "length": "number"
    }
  ]
}
```
| Field          | Type   | Description                  |
|----------------|--------|------------------------------|
| `status`       | string | Always `ok`.                 |
| `queues`       | array  | List of Redis queues and their lengths. |

#### Failure (500):
```json
{
  "status": "error",
  "message": "string"
}
```
| Field      | Type   | Description                 |
|------------|--------|-----------------------------|
| `status`   | string | Always `error`.             |
| `message`  | string | Error message.              |

---

## Error Codes
### 400 Bad Request
- Invalid input parameters.
- Missing required fields.

### 404 Not Found
- Resource not found (e.g., invalid video URL).

### 500 Internal Server Error
- Backend service failure.
- Redis or MongoDB unavailable.