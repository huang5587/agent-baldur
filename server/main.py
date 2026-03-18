import logging
import json
import sys
from urllib.parse import quote
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

from logging_config import setup_logging
from llm import query_llm, transcribe_audio
from party import is_party_update_request, extract_character_data
from tts import text_to_speech, enable_voice_clone

setup_logging()
logger = logging.getLogger(__name__)

# Enable voice clone if flag present (works with uvicorn reload)
if "--voice-clone" in sys.argv:
    enable_voice_clone()
    logger.info("Voice cloning enabled")

app = FastAPI()


@app.post("/ask")
async def ask(
    image: UploadFile = File(...),
    audio: UploadFile | None = File(None),
    text: str | None = Form(None),
):
    try:
        image_bytes = await image.read()

        # Get the question: either from text directly or by transcribing audio
        if text:
            question = text
        elif audio:
            audio_bytes = await audio.read()
            try:
                question = await transcribe_audio(audio_bytes)
            except Exception as e:
                logger.error("Transcription failed: %s", e)
                question = ""
        else:
            return {"error": "Must provide either 'text' or 'audio' field"}

        logger.info("Received question: %s", question[:100] if question else "(empty)")

        headers = {}
        answer = "Sorry, I couldn't process your request."

        # Check if this is a party update request
        if is_party_update_request(question):
            try:
                characters = await extract_character_data(image_bytes)
                valid_characters = [c for c in characters if c.get("name")]
                if valid_characters:
                    headers["X-Party-Update"] = quote(json.dumps(valid_characters))
                    names = [c["name"] for c in valid_characters]
                    if len(names) == 1:
                        answer = f"Added {names[0]} to your party file."
                    else:
                        answer = f"Added {len(names)} characters to your party: {', '.join(names)}."
                else:
                    answer = "I couldn't extract character data from this screenshot. Make sure you're showing the character sheet."
            except Exception as e:
                logger.error("Character extraction failed: %s", e)
                answer = "Failed to extract character data. Please try again with a clearer screenshot of the character sheet."
        else:
            # Regular game advice query
            try:
                answer = await query_llm(question, image_bytes)
            except Exception as e:
                logger.error("LLM query failed: %s", e)
                answer = "Sorry, I couldn't get advice right now. Please try again."

        # Convert answer to speech
        try:
            audio_path, media_type = await text_to_speech(answer)
            headers["X-Text-Response"] = quote(answer)

            ext = "wav" if "wav" in media_type else "aiff"
            return FileResponse(
                path=str(audio_path),
                media_type=media_type,
                filename=f"response.{ext}",
                headers=headers,
            )
        except Exception as e:
            logger.error("TTS synthesis failed: %s", e)
            return {"error": "Text-to-speech failed", "text_response": answer}

    except Exception as e:
        logger.exception("Unexpected error processing request")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    from config import SERVER_PORT

    uvicorn.run(app, host="127.0.0.1", port=SERVER_PORT)
