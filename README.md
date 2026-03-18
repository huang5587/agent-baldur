# Baldur's Gate 3 Voice Advisor

A voice-activated assistant for Baldur's Gate 3. Press a hotkey, ask a question, and get spoken advice based on your current game screen.

## How It Works

1. Press backtick (`) to start recording your question
2. Press backtick again to stop recording
3. The app captures a screenshot of the BG3 window
4. Your audio is transcribed and sent to an LLM along with the screenshot
5. The response is spoken back to you

## Requirements

- macOS 13.0+
- Python 3.10+
- OpenRouter API key

## Setup

1. Clone the repository and create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Create a `.env` file with your API key:

```bash
echo "OPENROUTER_API_KEY=your-key-here" > .env
```

3. Build the Swift hotkey listener:

```bash
cd baldur-assist
./build.sh
```

4. Grant Accessibility permissions when prompted (System Settings > Privacy & Security > Accessibility)

## Usage

```bash
./launch_assist.sh
```

### Hotkeys

- **Backtick (`)**: Start/stop recording
- **Escape**: Cancel recording
- **Ctrl+C**: Quit

### Voice Cloning (Optional)

For a custom cloned voice instead of macOS TTS:

```bash
./launch_assist.sh --voice-clone
```

Requires GPU/MPS and model checkpoints in `tts/checkpoints/`.

## Project Structure

```
baldur-assist/     # Swift hotkey listener and audio capture
server/            # Python FastAPI backend
  config.py        # Configuration constants
  llm.py           # OpenRouter API calls
  tts.py           # Text-to-speech (macOS say or voice clone)
  main.py          # HTTP endpoints
config.sh          # Shared shell configuration
launch_assist.sh   # Startup script
```
