from pymongo import MongoClient, ASCENDING, IndexModel
from datetime import datetime
from common.config import Config
from functools import lru_cache


@lru_cache(maxsize=None)
def get_db():
    client = MongoClient(Config.MONGO_URI)
    db = client.get_database()

    # Create indexes if they don't exist
    summaries_indexes = [
        IndexModel([("video_id", ASCENDING), ("settings.length", ASCENDING),
                    ("settings.focus_areas", ASCENDING), ("settings.language", ASCENDING)]),
        IndexModel([("updated_at", ASCENDING)])
    ]
    db.summaries.create_indexes(summaries_indexes)

    transcripts_indexes = [
        IndexModel([("video_id", ASCENDING), ("language", ASCENDING)], unique=True),
        IndexModel([("updated_at", ASCENDING)])
    ]
    db.transcripts.create_indexes(transcripts_indexes)

    return db


def save_to_db(video_id, settings, summary):
    db = get_db()
    normalized_settings = {
        "length": settings["length"],
        "focus_areas": sorted(settings["focus_areas"]),  # Sort for consistent lookup
        "language": settings["language"]
    }
    db.summaries.update_one(
        {"video_id": video_id, "settings": normalized_settings},
        {
            "$set": {
                "summary": summary,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )


def get_from_db(video_id, settings=None):
    db = get_db()
    if settings:
        normalized_settings = {
            "length": settings["length"],
            "focus_areas": sorted(settings["focus_areas"]),
            "language": settings["language"]
        }
        query = {"video_id": video_id, "settings": normalized_settings}
    else:
        query = {"video_id": video_id}

    result = db.summaries.find_one(query)
    return {
        "summary": result["summary"],
        "settings": result["settings"]
    } if result else None


def save_transcript_to_db(video_id, language, transcript):
    db = get_db()
    db.transcripts.update_one(
        {"video_id": video_id, "language": language},
        {
            "$set": {
                "transcript": transcript,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )


def get_transcript_from_db(video_id, language='en'):
    db = get_db()
    result = db.transcripts.find_one({
        "video_id": video_id,
        "language": language
    })
    return result["transcript"] if result else None
