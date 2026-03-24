import base64
import logging
import httpx
from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_CHAT_ENDPOINT,
    VISION_MODEL,
    TRANSCRIPTION_MODEL,
    SYSTEM_PROMPT,
    LLM_TIMEOUT_SECONDS,
    TRANSCRIPTION_TIMEOUT_SECONDS,
    TRANSCRIPTION_PROMPT,
)

logger = logging.getLogger(__name__)


async def query_llm(question: str, image_bytes: bytes, party_context: str = "", decisions_context: str = "") -> str:
    logger.debug("Querying LLM with model=%s, image_size=%d bytes", VISION_MODEL, len(image_bytes))
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    system = SYSTEM_PROMPT
    if party_context:
        system += f"\n\nThe user's current party:\n{party_context}"
    if decisions_context:
        system += f"\n\nKey narrative decisions made so far:\n{decisions_context}"

    messages = [
        {"role": "system", "content": system},
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

    async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}{OPENROUTER_CHAT_ENDPOINT}",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": messages,
            },
        )
        data = resp.json()
        if resp.status_code != 200:
            logger.error("LLM API error (HTTP %d): %s", resp.status_code, data)
            resp.raise_for_status()
        if "choices" not in data:
            logger.error("LLM response missing 'choices'. model=%s, response=%s", VISION_MODEL, data)
            raise ValueError(f"Unexpected LLM response: {data}")
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
                    "text": TRANSCRIPTION_PROMPT,
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

    async with httpx.AsyncClient(timeout=TRANSCRIPTION_TIMEOUT_SECONDS) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}{OPENROUTER_CHAT_ENDPOINT}",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": TRANSCRIPTION_MODEL,
                "messages": messages,
            },
        )
        data = resp.json()
        if resp.status_code != 200:
            logger.error("Transcription API error (HTTP %d): %s", resp.status_code, data)
            resp.raise_for_status()
        if "choices" not in data:
            logger.error("Transcription response missing 'choices'. model=%s, response=%s", TRANSCRIPTION_MODEL, data)
            raise ValueError(f"Unexpected transcription response: {data}")
        transcript = data["choices"][0]["message"]["content"]
        logger.debug("Transcription complete: %d chars", len(transcript))
        return transcript
