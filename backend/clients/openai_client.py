import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or None

RECOMMENDATION_MODEL = os.getenv("OPENAI_RECOMMENDATION_MODEL", "gpt-5-mini")
TAGGER_MODEL = os.getenv("OPENAI_TAGGER_MODEL", "gpt-5-nano")

OPENCODE_SESSION_ID = "ses_ai_movie_recommender"
default_headers = {"x-opencode-session": OPENCODE_SESSION_ID}

openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
    default_headers=default_headers,
)
