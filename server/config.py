import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Voice cloning configuration
VOICE_CLONE_CHECKPOINT_DIR = Path(__file__).parent.parent / "tts" / "checkpoints" / "s1-mini"
VOICE_CLONE_REFERENCE_AUDIO = Path(__file__).parent.parent / "tts" / "examples" / "ian_speech_clip.mp3"
VOICE_CLONE_REFERENCE_TEXT = Path(__file__).parent.parent / "tts" / "examples" / "ian_transcript.txt"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# HTTP Timeouts
LLM_TIMEOUT_SECONDS = 60.0
TRANSCRIPTION_TIMEOUT_SECONDS = 30.0

# API Endpoints
OPENROUTER_CHAT_ENDPOINT = "/chat/completions"

# Media Types
MEDIA_TYPE_WAV = "audio/wav"
MEDIA_TYPE_AIFF = "audio/aiff"

# TTS
MACOS_VOICE = "Moira"

# Prompts
TRANSCRIPTION_PROMPT = "Transcribe this audio exactly. Return only the transcription, nothing else."

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

# Save management
DEFAULT_SAVE_NAME = "default"

SAVE_SWITCH_KEYWORDS = [
    "switch to save", "load save", "switch save", "use save",
]
SAVE_LIST_KEYWORDS = [
    "list saves", "list my saves", "show saves", "what saves",
]
SAVE_CREATE_KEYWORDS = [
    "create save", "new save", "create a save", "make a save",
]

PARTY_UPDATE_KEYWORDS = [
    "add to party", "add to my party", "save to party", "save character",
    "update party", "update my party", "add this character", "save this character",
    "add them to my party", "add her to my party", "add him to my party",
    "save my party", "save party", "save all characters", "add my party"
]

DECISION_RECORD_KEYWORDS = [
    "record decision", "save decision", "remember that", "note that I",
    "record that", "log that", "remember I", "note that we",
    "record that I", "record that we", "save that I", "save that we",
]

DECISION_EXTRACTION_PROMPT = """\
The user wants to record a narrative decision they made in Baldur's Gate 3.
Extract the decision from their statement and return ONLY valid JSON (no markdown, no explanation):
{{"decision": "short summary of the decision", "context": "brief additional context if any"}}

User statement: {statement}
"""

DECISION_DETECT_PROMPT = """\
The user asked the following question about Baldur's Gate 3. Determine if their question \
implies they have made a specific narrative decision or choice in the game.

Examples of implied decisions:
- "What happens now that I betrayed the grove?" implies: betrayed the Emerald Grove
- "I sided with the goblins, what should I do next?" implies: sided with the goblins
- "Should I go to the Underdark?" implies: NO decision (just asking for advice)

If a decision IS implied, return ONLY valid JSON (no markdown):
{{"decision": "short summary", "context": "brief context"}}

If NO decision is implied, return exactly: null

User question: {question}
"""

SERVER_PORT = 8787
