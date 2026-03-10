import base64
import httpx
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, VISION_MODEL, TRANSCRIPTION_MODEL, SYSTEM_PROMPT


async def query_llm(question: str, image_bytes: bytes) -> str:
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
        return data["choices"][0]["message"]["content"]


async def transcribe_audio(audio_bytes: bytes) -> str:
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
        return data["choices"][0]["message"]["content"]
