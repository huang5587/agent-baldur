import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Voice cloning configuration
VOICE_CLONE_ENABLED = os.environ.get("VOICE_CLONE_ENABLED", "").lower() in ("1", "true", "yes")
VOICE_CLONE_CHECKPOINT_DIR = Path(__file__).parent.parent / "tts" / "checkpoints" / "s1-mini"
VOICE_CLONE_REFERENCE_AUDIO = Path(__file__).parent.parent / "tts" / "examples" / "ian_speech_clip.mp3"
VOICE_CLONE_REFERENCE_TEXT = Path(__file__).parent.parent / "tts" / "examples" / "ian_transcript.txt"
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

CHARACTER_EXTRACTION_PROMPT_TEMPLATE = """\
Extract ALL party members from this Baldur's Gate 3 screenshot.
Return ONLY a valid JSON array of characters (no markdown, no explanation).

Each character should match this schema:
{schema}

Extract all visible information for each party member. Use null for fields not visible.
For skills, set true if the character is proficient (look for filled circles or checkmarks).
For arrays, extract all visible items. For booleans, use true/false.

Return format: [{{character1}}, {{character2}}, ...]
"""

# Path to party.json (relative to server directory)
PARTY_JSON_PATH = "../baldur-assist/party.json"

PARTY_UPDATE_KEYWORDS = [
    "add to party", "add to my party", "save to party", "save character",
    "update party", "update my party", "add this character", "save this character",
    "add them to my party", "add her to my party", "add him to my party",
    "save my party", "save party", "save all characters", "add my party"
]

SERVER_PORT = 8787
