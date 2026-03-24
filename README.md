# Baldur's Gate 3 Voice Advisor

A voice-activated AI assistant for Baldur's Gate 3. Press a hotkey while playing, ask a question, and get spoken game advice informed by your current screen, party composition, and past narrative decisions -- all without leaving the game.

## Architecture

The system is a two-tier client/server application:

```
Swift macOS Client (baldur-assist)
    | multipart POST (audio WAV + screenshot PNG)
    v
Python FastAPI Server (localhost:8787)
    | OpenRouter API calls
    v
LLM (Xiaomi MiMo-V2-Omni / Qwen 3.5 fallback)
```

The **Swift client** registers a global CGEvent tap for hotkey detection, records audio via AVAudioEngine, captures the BG3 window via CGWindowListCreateImage, and sends both as multipart form data to the server. The **Python server** transcribes the audio, determines intent via keyword matching, queries a multimodal LLM with the screenshot and accumulated game context, then returns a synthesized audio response.

## Features

### Voice-Activated Game Advice

Press backtick to start recording, press again to stop. The app captures a screenshot of the active BG3 window (with full-screen fallback), transcribes your question via OpenRouter's GPT-Audio model, and sends both to a vision LLM. The response is converted to speech and played back. Press Escape to abort a recording.

### Party Management

Say "add to my party" while viewing a character sheet. The server sends the screenshot to the vision model with a structured extraction prompt, parses the returned JSON (ability scores, class, race, level, skills, proficiencies, spells, equipment), and merges it into the active save's `party.json`. Party data is included as context in all subsequent advice queries.

### Decision Tracking

Narrative choices are tracked in two ways:

- **Explicit**: Say "record that I sided with the goblins" and the server extracts a structured decision + context via the LLM and appends it to `decisions.json`.
- **Implicit**: When a regular advice query implies a past decision (e.g., "what now that I betrayed the grove?"), the server auto-detects and records it.

Recorded decisions are fed as context to all future LLM queries, giving the advisor memory of your playthrough.

### Multi-Save Support

Voice commands manage independent save slots, each with its own party roster and decision log:

- "Create save honor-mode" / "Switch to save honor-mode" / "List saves"
- Save data is stored in `saves/<name>/` as JSON files.

### Voice Cloning (Optional)

Fish Audio S1-Mini can be used for custom voice synthesis instead of macOS TTS. Requires GPU/MPS and pre-downloaded model checkpoints in `tts/checkpoints/`. Falls back to the macOS `say` command when unavailable.

### Model Fallback

LLM queries use Xiaomi MiMo-V2-Omni as the primary multimodal model. If it fails, the server automatically retries with Qwen 3.5 122B as a fallback.

## Requirements

- macOS 13.0+
- Python 3.10+
- Swift 5.9+
- OpenRouter API key

## Setup

1. Create a virtual environment and install dependencies:

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
cd baldur-assist && ./build.sh
```

4. Grant Accessibility permissions when prompted (System Settings > Privacy & Security > Accessibility).

### Voice Cloning (Optional)

For a custom cloned voice instead of macOS TTS:

```bash
./launch_assist.sh --voice-clone
```

Requires GPU/MPS and model checkpoints in `tts/checkpoints/`.

## Usage

```bash
./launch_assist.sh [--voice-clone] [--save <name>]
```

The launch script starts the FastAPI server on port 8787, waits for it to become ready, then launches the Swift hotkey app. Ctrl+C tears down both processes.

### Hotkeys

- **Backtick (`)** -- Start/stop recording
- **Escape** -- Cancel recording
- **Ctrl+C** -- Quit

## Project Structure

```
baldur-assist/                  # Swift macOS client
  Sources/
    main.swift                  # CGEvent tap, hotkey handling, main loop
    AudioRecorder.swift         # AVAudioEngine recording (16kHz mono WAV)
    ScreenCapture.swift         # BG3 window capture with full-screen fallback
    ServerClient.swift          # HTTP POST + audio playback
    Constants.swift             # Keycodes, URLs, timeouts
    ProjectPaths.swift          # Path resolution relative to executable
  Package.swift
  build.sh

server/                         # Python FastAPI backend
  main.py                       # /ask endpoint, intent routing
  llm.py                        # OpenRouter API client (transcription + multimodal queries)
  tts.py                        # TTS abstraction (macOS say / Fish Audio voice clone)
  config.py                     # Models, prompts, keywords, timeouts
  party.py                      # Character extraction, decision recording
  save_manager.py               # Save slot CRUD, JSON file I/O
  logging_config.py             # Centralized logging

saves/                          # Game state persistence (JSON)
  template/party.json           # Character schema template
  default/                      # Default save slot
    party.json
    decisions.json

launch_assist.sh                # Startup script (server + client)
config.sh                       # Shared shell configuration
```
