from urllib.parse import urlparse, parse_qs

from utils.logger import logger


# api/utils.py
def extract_video_id(url):
    try:
        if "youtube.com" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be" in url:
            return url.split("/")[-1]
        else:
            raise ValueError("Invalid YouTube URL format")
    except Exception as e:
        raise ValueError(f"Error extracting video ID: {e}")


def validate_youtube_url(url):
    """Validate and extract video ID from YouTube URL."""
    try:
        parsed_url = urlparse(url.strip())
        if parsed_url.hostname not in ['www.youtube.com', 'youtube.com', 'youtu.be']:
            logger.warning(f"Invalid hostname: {parsed_url.hostname}")
            return None

        video_id = None
        if parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path[1:]
        elif 'watch' in parsed_url.path:
            query_params = parse_qs(parsed_url.query)
            video_id = query_params.get('v', [None])[0]

        logger.info(f"Extracted video ID: {video_id} from URL: {url}")
        return video_id
    except Exception as e:
        logger.error(f"Error parsing YouTube URL: {url}, Error: {str(e)}")
        return None
