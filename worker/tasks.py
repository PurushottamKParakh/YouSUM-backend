from celery import chain
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from common.config import Config
from common.db import save_to_db, save_transcript_to_db, get_transcript_from_db
from celery.utils.log import get_task_logger
from worker.celery_app import celery

logger = get_task_logger(__name__)


class APIKeyError(Exception):
    pass


def get_openai_client():
    if not Config.OPENAI_API_KEY:
        raise APIKeyError("OpenAI API key not found")
    return OpenAI(api_key=Config.OPENAI_API_KEY)


@celery.task(bind=True, name='worker.tasks.fetch_transcript', retry_backoff=True, max_retries=3)
def fetch_transcript(self, video_id, language='en'):
    logger.info(f"Checking transcript for video {video_id} in {language}")

    # Check db first
    cached_transcript = get_transcript_from_db(video_id, language)
    if cached_transcript:
        logger.info(f"Using cached transcript for {video_id}")
        return cached_transcript

    # Fetch if not in db
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript([language])
        except:
            logger.info(f"Falling back to English transcript")
            transcript = transcript_list.find_transcript(['en'])
            language = 'en'

        transcript_parts = transcript.fetch()
        transcript_text = " ".join([entry["text"] for entry in transcript_parts])
        save_transcript_to_db(video_id, language, transcript_text)
        return transcript_text
    except Exception as e:
        logger.error(f"Transcript fetch error: {str(e)}")
        self.retry(exc=e)


@celery.task(name='worker.tasks.save_summary')
def save_summary(summary, video_id, settings):
    save_to_db(video_id, settings, summary)
    return {"summary": summary, "settings": settings}


@celery.task(bind=True, name='worker.tasks.process_video', retry_backoff=True, max_retries=3)
def process_video(self, video_id, settings):
    logger.info(f"Processing video {video_id}")
    try:
        # Check if transcript exists first in database
        cached_transcript = get_transcript_from_db(video_id, settings['language'])
        if cached_transcript:
            logger.info(f"Using existing transcript for {video_id}")
            workflow = chain(
                generate_summary.s(cached_transcript, settings),
                save_summary.s(video_id, settings)
            )
        else:
            workflow = chain(
                fetch_transcript.s(video_id, settings['language']),
                generate_summary.s(settings),
                save_summary.s(video_id, settings)
            )
        return workflow.apply_async()
    except Exception as e:
        logger.error(f"Video processing error: {str(e)}")
        self.retry(exc=e)


@celery.task(bind=True, name='worker.tasks.generate_summary', retry_backoff=True, max_retries=2)
def generate_summary(self, transcript, settings):
    logger.info("Generating summary with settings: " + str(settings))
    try:
        client = get_openai_client()
        length_map = {
            "short": "less than 100 words",
            "medium": "less than 150 words",
            "long": "less than 300 words"
        }
        focus_map = {
            "technical_details": "technical specifications, methodologies",
            "key_points": "main arguments, core concepts",
            "action_items": "actionable steps, recommendations",
            "balanced_overview": "paragraph with balanced view"
        }
        focus_text = ", ".join(focus_map[area] for area in settings['focus_areas']) or "balanced_overview"
        user_prompt = f"""Generate a {length_map[settings['length']]} summary in {settings['language']} language. Length is very important. Focus on: {focus_text}
                    Format the response as follows:
                    1. Genre: [one-word genre] in {settings['language']} language.
                    2. Emotion/tone: [one-word emotion] {settings['language']} language.
                    3. Point-wise Summary: write in {settings['language']} language and [focused on {focus_text}] but in case of balanced_overview it should be a paragraph as in Summary:.... 
                    4. Key takeaway: [1-2 line essence of what should be learned] in {settings['language']} language.
                Here is the transcript: {transcript} in English language."""

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system",
                 "content": "You are an advanced assistant that processes video transcripts to provide detailed insights."},
                {"role": "user", "content": f"Summarize: {user_prompt}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Summary generation error: {str(e)}")
        self.retry(exc=e)
