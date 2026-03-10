import json
from urllib.parse import quote
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

from llm import query_llm, transcribe_audio
from party import is_party_update_request, extract_character_data
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

    headers = {}

    # Check if this is a party update request
    if is_party_update_request(question):
        try:
            character_data = await extract_character_data(image_bytes)
            if character_data and character_data.get("name"):
                headers["X-Party-Update"] = quote(json.dumps(character_data))
                answer = f"Added {character_data['name']} to your party file."
            else:
                answer = "I couldn't extract character data from this screenshot. Make sure you're showing the character sheet."
        except Exception as e:
            print(f"[server] Character extraction failed: {e}")
            answer = "Failed to extract character data. Please try again with a clearer screenshot of the character sheet."
    else:
        # Regular game advice query
        answer = await query_llm(question, image_bytes)

    # Convert answer to speech
    audio_path = await text_to_speech(answer)
    headers["X-Text-Response"] = quote(answer)

    return FileResponse(
        path=str(audio_path),
        media_type="audio/aiff",
        filename="response.aiff",
        headers=headers,
    )


if __name__ == "__main__":
    import uvicorn
    from config import SERVER_PORT

    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT)
