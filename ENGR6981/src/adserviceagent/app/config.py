# /srv/app/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    APP_NAME = os.getenv("APP_NAME", "adserviceagent")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("APP_PORT", "8086"))

    ADSERVICE_HOST = os.getenv("ADSERVICE_HOST", "localhost")
    ADSERVICE_PORT = int(os.getenv("ADSERVICE_PORT", "9555"))

    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    MODEL_NAME = os.getenv("MODEL_NAME", "qwen3:latest")
    USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

# This must exist at the bottom of config.py
settings = Settings()
ADSERVICE_HOST = settings.ADSERVICE_HOST
ADSERVICE_PORT = settings.ADSERVICE_PORT
APP_NAME = settings.APP_NAME
APP_HOST = settings.APP_HOST
APP_PORT = settings.APP_PORT

ADSERVICE_HOST = settings.ADSERVICE_HOST
ADSERVICE_PORT = settings.ADSERVICE_PORT

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_MODEL = settings.MODEL_NAME          # qwen.py expects this name
MODEL_NAME = settings.MODEL_NAME
USE_LLM = settings.USE_LLM
