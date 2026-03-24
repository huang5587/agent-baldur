import logging
import sys
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

from logging_config import setup_logging
from llm import query_llm, transcribe_audio
from party import (
    is_party_update_request,
    is_decision_record_request,
    parse_save_command,
    extract_character_data,
    extract_decision,
    detect_implicit_decision,
)
from tts import text_to_speech, enable_voice_clone
from config import MEDIA_TYPE_WAV
import save_manager

setup_logging()
logger = logging.getLogger(__name__)

# Enable voice clone if flag present (works with uvicorn reload)
if "--voice-clone" in sys.argv:
    enable_voice_clone()
    logger.info("Voice cloning enabled")

# Set initial save from CLI flag
if "--save" in sys.argv:
    idx = sys.argv.index("--save")
    if idx + 1 < len(sys.argv):
        save_manager.switch_save(sys.argv[idx + 1])
        logger.info("Initial save: %s", save_manager.get_active_save())
else:
    save_manager.switch_save(save_manager.get_active_save())
    logger.info("Using default save: %s", save_manager.get_active_save())

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

        answer = "Sorry, I couldn't process your request."

        # Check if this is a save management command
        save_cmd = parse_save_command(question)
        if save_cmd:
            action, name = save_cmd
            if action == "switch":
                answer = save_manager.switch_save(name)
            elif action == "create":
                answer = save_manager.create_save(name)
            elif action == "list":
                saves = save_manager.list_saves()
                active = save_manager.get_active_save()
                if saves:
                    answer = f"Your saves are: {', '.join(saves)}. Currently using {active}."
                else:
                    answer = f"No saves found. Currently using {active}."
        # Check if this is a decision recording request
        elif is_decision_record_request(question):
            try:
                decision = await extract_decision(question)
                if decision:
                    save_manager.add_decision(decision)
                    answer = f"Recorded: {decision['decision']}."
                else:
                    answer = "I couldn't understand the decision. Try rephrasing."
            except Exception as e:
                logger.error("Decision extraction failed: %s", e)
                answer = "Failed to record the decision. Please try again."
        # Check if this is a party update request
        elif is_party_update_request(question):
            try:
                characters = await extract_character_data(image_bytes)
                valid_characters = [c for c in characters if c.get("name")]
                if valid_characters:
                    save_manager.update_party(valid_characters)
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
                party_context = save_manager.load_party_context()
                decisions_context = save_manager.load_decisions_context()
                answer = await query_llm(question, image_bytes, party_context, decisions_context)

                # Auto-detect implicit decisions from the query
                try:
                    decision = await detect_implicit_decision(question)
                    if decision:
                        save_manager.add_decision(decision)
                        logger.info("Auto-recorded decision: %s", decision["decision"])
                except Exception as e:
                    logger.warning("Implicit decision detection failed: %s", e)
            except Exception as e:
                logger.error("LLM query failed: %s", e)
                answer = "Sorry, I couldn't get advice right now. Please try again."

        # Convert answer to speech
        try:
            audio_path, media_type = await text_to_speech(answer)

            ext = "wav" if media_type == MEDIA_TYPE_WAV else "aiff"
            return FileResponse(
                path=str(audio_path),
                media_type=media_type,
                filename=f"response.{ext}",
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
