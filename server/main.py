import os
from urllib.parse import quote
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

from llm import query_llm, transcribe_audio
from tts import text_to_speech

app = FastAPI()


@app.post("/ask")
async def ask(
    image: UploadFile = File(...),
    audio: UploadFile | None = File(None),
    text: str | None = Form(None),
):
    image_bytes = await image.read()

    # Get the question: either from text directly or by transcribing audio
    if text:
        question = text
    elif audio:
        audio_bytes = await audio.read()
        question = await transcribe_audio(audio_bytes)
    else:
        return {"error": "Must provide either 'text' or 'audio' field"}

    # Query the multimodal LLM
    answer = await query_llm(question, image_bytes)

    # Convert answer to speech
    audio_path = await text_to_speech(answer)

    return FileResponse(
        path=str(audio_path),
        media_type="audio/aiff",
        filename="response.aiff",
        headers={"X-Text-Response": quote(answer)},
    )


if __name__ == "__main__":
    import uvicorn
    from config import SERVER_PORT

    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT)
