# api/routes.py
import redis
from flask import Blueprint, request, jsonify, current_app
from worker.celery_app import celery
from http import HTTPStatus
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.logger import logger
from utils.utils import validate_youtube_url
from common.db import get_from_db, get_transcript_from_db

celery.autodiscover_tasks(["worker.tasks"], force=True)
api_bp = Blueprint("api", __name__)
limiter = Limiter(
    get_remote_address,
    app=None,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://redis:6379/2"
)


@api_bp.route("/transcript", methods=["GET"])
@limiter.limit("100/day;30/hour")
def get_transcript():
    client_ip = get_remote_address()
    logger.info(f"New transcript request from IP: {client_ip}")

    url = request.args.get("url")
    language = request.args.get("language", "en")

    if not url:
        logger.warning(f"Missing URL parameter from IP: {client_ip}")
        return jsonify({
            "status": "error",
            "message": "URL parameter is required"
        }), HTTPStatus.BAD_REQUEST

    video_id = validate_youtube_url(url)
    if not video_id:
        logger.warning(f"Invalid YouTube URL: {url} from IP: {client_ip}")
        return jsonify({
            "status": "error",
            "message": "Invalid YouTube URL"
        }), HTTPStatus.BAD_REQUEST

    cached_transcript = get_transcript_from_db(video_id, language)
    if cached_transcript:
        logger.info(f"Cache hit for transcript video ID: {video_id}, language: {language}")
        return jsonify({
            "status": "completed",
            "result": cached_transcript,
            "language": language,
            "cached": True,
            "video_id": video_id
        })

    try:
        logger.info(f"Cache miss for transcript video ID: {video_id}, language: {language}")
        task = celery.signature('worker.tasks.fetch_transcript', args=[video_id, language]).delay()
        return jsonify({
            "status": "processing",
            "video_id": video_id,
            "language": language,
            "result_url": f"/api/transcript/result/{video_id}?language={language}"
        }), HTTPStatus.ACCEPTED
    except Exception as e:
        logger.error(f"Failed to fetch transcript for video ID: {video_id}, Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to start processing: {str(e)}"
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route("/transcript/result/<video_id>", methods=["GET"])
@limiter.limit("300/day;60/hour")
def get_transcript_result(video_id):
    client_ip = get_remote_address()
    language = request.args.get("language", "en")
    logger.info(f"Transcript result request for video ID: {video_id}, language: {language} from IP: {client_ip}")

    try:
        transcript = get_transcript_from_db(video_id, language)
        if transcript:
            logger.info(f"Transcript found for video ID: {video_id}, language: {language}")
            return jsonify({
                "status": "completed",
                "result": transcript,
                "language": language,
                "video_id": video_id
            })

        logger.info(f"Transcript still processing for video ID: {video_id}")
        return jsonify({
            "status": "processing",
            "video_id": video_id,
            "language": language
        }), HTTPStatus.ACCEPTED

    except Exception as e:
        logger.error(f"Error fetching transcript result for video ID: {video_id}, Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch result: {str(e)}"
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route("/summarize", methods=["GET"])
@limiter.limit("100/day;30/hour")
def summarize():
    client_ip = get_remote_address()
    logger.info(f"New summary request from IP: {client_ip}")

    url = request.args.get("url")
    settings = {
        "length": request.args.get("length", "medium"),
        "focus_areas": request.args.getlist("focus_areas") or ["key_points"],
        "language": request.args.get("language", "en")
    }

    if not url:
        logger.warning(f"Missing URL parameter from IP: {client_ip}")
        return jsonify({
            "status": "error",
            "message": "URL parameter is required"
        }), HTTPStatus.BAD_REQUEST

    if settings["length"] not in ["short", "medium", "long"]:
        return jsonify({
            "status": "error",
            "message": "Invalid length. Must be 'short', 'medium', or 'long'"
        }), HTTPStatus.BAD_REQUEST

    valid_areas = ["technical_details", "key_points", "action_items", "balanced_overview"]
    if not all(area in valid_areas for area in settings["focus_areas"]):
        return jsonify({
            "status": "error",
            "message": f"Invalid focus areas. Must be one or more of: {valid_areas}"
        }), HTTPStatus.BAD_REQUEST

    video_id = validate_youtube_url(url)
    if not video_id:
        logger.warning(f"Invalid YouTube URL: {url} from IP: {client_ip}")
        return jsonify({
            "status": "error",
            "message": "Invalid YouTube URL"
        }), HTTPStatus.BAD_REQUEST

    cached_summary = get_from_db(video_id, settings)
    if cached_summary:
        logger.info(f"Cache hit for video ID: {video_id}")
        return jsonify({
            "status": "completed",
            "result": cached_summary["summary"],
            "settings": cached_summary["settings"],
            "cached": True,
            "video_id": video_id
        })

    try:
        logger.info(f"Cache miss for video ID: {video_id}, starting processing with settings: {settings}")
        task = celery.signature('worker.tasks.process_video', args=[video_id, settings]).delay()
        return jsonify({
            "task_id": task.id,
            "status": "processing",
            "video_id": video_id,
            "settings": settings,
            "result_url": f"/api/result/{video_id}?length={settings['length']}&language={settings['language']}&{'&'.join(f'focus_areas={area}' for area in settings['focus_areas'])}"
        }), HTTPStatus.ACCEPTED
    except Exception as e:
        logger.error(f"Failed to process video ID: {video_id}, Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to start processing: {str(e)}"
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route("/result/<video_id>", methods=["GET"])
@limiter.limit("300/day;60/hour")
def get_result(video_id):
    client_ip = get_remote_address()
    settings = {
        "length": request.args.get("length", "medium"),
        "focus_areas": request.args.getlist("focus_areas") or ["key_points"],
        "language": request.args.get("language", "en")
    }
    logger.info(f"Result request for video ID: {video_id} from IP: {client_ip}")

    try:
        result = get_from_db(video_id, settings)
        if result:
            logger.info(f"Summary found for video ID: {video_id}")
            return jsonify({
                "status": "completed",
                "result": result["summary"],
                "settings": result["settings"],
                "video_id": video_id
            })

        logger.info(f"Summary still processing for video ID: {video_id}")
        return jsonify({
            "status": "processing",
            "video_id": video_id
        }), HTTPStatus.ACCEPTED

    except Exception as e:
        logger.error(f"Error fetching result for video ID: {video_id}, Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to fetch result: {str(e)}"
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route("/result/<task_id>", methods=["GET"])
def get_task_result(task_id):
    task_result = celery.AsyncResult(task_id)

    if not task_result.ready():
        return jsonify({"status": "processing"}), HTTPStatus.ACCEPTED

    if task_result.failed():
        return jsonify({
            "status": "failed",
            "error": str(task_result.result)
        }), HTTPStatus.INTERNAL_SERVER_ERROR

    return jsonify({
        "status": "completed",
        "result": task_result.get()
    })


@api_bp.route("/status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    task_result = celery.AsyncResult(task_id)

    result = {
        "task_id": task_id,
        "status": task_result.state,
        "result_url": f"/api/result/{task_id}" if task_result.ready() else None,
        "info": {
            "successful": task_result.successful() if task_result.ready() else None,
            "failed": task_result.failed() if task_result.ready() else None,
            "ready": task_result.ready(),
        }
    }

    if task_result.failed():
        result["error"] = str(task_result.result)

    return jsonify(result)


@api_bp.route("/redis-health", methods=["GET"])
def redis_health():
    try:
        broker_url = current_app.config['CELERY_BROKER_URL']
        r = redis.from_url(broker_url, socket_timeout=5, socket_connect_timeout=5)
        broker_ping = r.ping()

        backend_url = current_app.config['CELERY_RESULT_BACKEND']
        r_backend = redis.from_url(backend_url, socket_timeout=5, socket_connect_timeout=5)
        backend_ping = r_backend.ping()

        return jsonify({
            "status": "healthy",
            "broker": {
                "connected": broker_ping,
                "info": r.info(section="server")
            },
            "backend": {
                "connected": backend_ping,
                "info": r_backend.info(section="server")
            }
        }), HTTPStatus.OK
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "error_type": type(e).__name__
        }), HTTPStatus.INTERNAL_SERVER_ERROR


@api_bp.route("/redis-debug", methods=["GET"])
def redis_debug():
    try:
        broker_url = current_app.config['CELERY_BROKER_URL']
        backend_url = current_app.config['CELERY_RESULT_BACKEND']

        broker_redis = redis.from_url(broker_url)
        backend_redis = redis.from_url(backend_url)

        broker_keys = broker_redis.keys('*')
        backend_keys = backend_redis.keys('*')

        task_keys = [key for key in backend_keys if key.startswith(b'celery-task')]

        task_values = {}
        for key in task_keys:
            try:
                value = backend_redis.get(key)
                task_values[key.decode('utf-8')] = value.decode('utf-8') if value else None
            except Exception as e:
                task_values[key.decode('utf-8')] = f"Error reading value: {str(e)}"

        return jsonify({
            "broker_connection": {
                "url": broker_url,
                "connected": broker_redis.ping(),
                "keys": [k.decode('utf-8') for k in broker_keys],
            },
            "backend_connection": {
                "url": backend_url,
                "connected": backend_redis.ping(),
                "keys": [k.decode('utf-8') for k in backend_keys],
            },
            "task_values": task_values
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }), HTTPStatus.INTERNAL_SERVER_ERROR
