# common/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Determine the root directory of the project
ROOT_DIR = Path(__file__).parent.parent


# Load environment variables from the appropriate .env file
def load_environment():
    """Load environment variables from the appropriate .env file"""
    env_files = [
        os.path.join(ROOT_DIR, '.env'),  # Local development
        os.path.join(ROOT_DIR, '.env.production'),  # Production
    ]

    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file)
            print(f"Loaded environment from: {env_file}")
            break
    else:
        raise EnvironmentError("No .env file found! Please create one based on .env.example")


# Load environment variables
load_environment()


class Config:
    """Application configuration class"""
    # Required settings - will raise error if not set
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY must be set in environment variables")

    # Optional settings with defaults
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/youtube_summary')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/1')

    # Flask settings
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'

    @classmethod
    def validate(cls):
        """Validate the configuration"""
        required_settings = [
            ('OPENAI_API_KEY', cls.OPENAI_API_KEY),
            ('MONGO_URI', cls.MONGO_URI),
            ('REDIS_URL', cls.REDIS_URL),
        ]

        missing = [name for name, value in required_settings if not value]

        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                "Please check your environment variables and .env file."
            )