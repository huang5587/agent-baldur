import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Multimodal model for game advice
VISION_MODEL = "qwen/qwen3.5-122b-a10b"

# Audio model for transcription
TRANSCRIPTION_MODEL = "openai/gpt-audio"

SYSTEM_PROMPT = (
    "You are a concise game advisor for Baldur's Gate 3. The user is actively playing "
    "and will send you a screenshot of their current game state along with a spoken "
    "question. Give brief, actionable advice. Reference what you see in the screenshot "
    "when relevant. Keep responses under 3 sentences unless the question requires more detail."
)

SERVER_PORT = 8787
