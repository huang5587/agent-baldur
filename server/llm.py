import base64
import logging
import httpx
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, VISION_MODEL, TRANSCRIPTION_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


async def query_llm(question: str, image_bytes: bytes) -> str:
    logger.debug("Querying LLM with model=%s, image_size=%d bytes", VISION_MODEL, len(image_bytes))
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                    },
                },
                {
                    "type": "text",
                    "text": question,
                },
            ],
        },
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        logger.debug("LLM response received: %d chars", len(content))
        return content


async def transcribe_audio(audio_bytes: bytes) -> str:
    logger.debug("Transcribing audio: %d bytes", len(audio_bytes))
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Transcribe this audio exactly. Return only the transcription, nothing else.",
                },
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": audio_b64,
                        "format": "wav",
                    },
                },
            ],
        },
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": TRANSCRIPTION_MODEL,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        transcript = data["choices"][0]["message"]["content"]
        logger.debug("Transcription complete: %d chars", len(transcript))
        return transcript
