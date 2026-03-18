"""
Text-to-Speech Module

Supports two backends:
- macOS say (default): Fast, uses system voice
- Fish Audio (--voice-clone): Cloned voice, requires GPU/MPS
"""

import asyncio
import logging
import subprocess
import sys
import tempfile
from pathlib import Path

from config import (
    VOICE_CLONE_CHECKPOINT_DIR,
    VOICE_CLONE_REFERENCE_AUDIO,
    VOICE_CLONE_REFERENCE_TEXT,
    MACOS_VOICE,
    MEDIA_TYPE_WAV,
    MEDIA_TYPE_AIFF,
)

logger = logging.getLogger(__name__)

# Voice cloning state
_voice_clone_enabled = False
_voice_cloner: "VoiceCloner | None" = None


def enable_voice_clone():
    """Enable voice cloning mode. Call before first text_to_speech() call."""
    global _voice_clone_enabled
    _voice_clone_enabled = True


class VoiceCloner:
    """Fish Audio voice cloning with pre-loaded models."""

    def __init__(self, checkpoint_dir: Path, reference_audio: Path, reference_text_path: Path):
        logger.debug("Python executable: %s", sys.executable)

        # Add tts directory to path for fish_tts_core import
        tts_dir = str(checkpoint_dir.parent.parent)
        if tts_dir not in sys.path:
            sys.path.insert(0, tts_dir)

        from fish_tts_core import (
            get_device,
            extract_reference_tokens,
            load_codec_model,
            load_semantic_model,
        )

        self.device = get_device()
        self.checkpoint_dir = checkpoint_dir

        # Load reference transcript
        self.reference_text = reference_text_path.read_text().strip()
        logger.debug("Reference transcript loaded: %d chars", len(self.reference_text))

        logger.info("Loading TTS models on device=%s", self.device)

        # Pre-load models (cached in fish_tts_core)
        load_codec_model(checkpoint_dir, self.device)
        load_semantic_model(checkpoint_dir, self.device)

        # Pre-extract reference voice
        logger.debug("Extracting voice features from %s", reference_audio.name)
        self.reference_tokens = extract_reference_tokens(
            reference_audio, checkpoint_dir, self.device
        )

        logger.info("Voice cloning initialized")

    def synthesize_sync(self, text: str) -> Path:
        """Blocking synthesis. Call via asyncio.to_thread()."""
        from fish_tts_core import synthesize

        return synthesize(
            text=text,
            reference_tokens=self.reference_tokens,
            reference_text=self.reference_text,
            checkpoint_dir=self.checkpoint_dir,
            device=self.device
        )


def _get_voice_cloner() -> VoiceCloner | None:
    """Get or initialize voice cloner (lazy loading)."""
    global _voice_cloner

    if not _voice_clone_enabled:
        return None

    if _voice_cloner is None:
        try:
            _voice_cloner = VoiceCloner(
                VOICE_CLONE_CHECKPOINT_DIR,
                VOICE_CLONE_REFERENCE_AUDIO,
                VOICE_CLONE_REFERENCE_TEXT
            )
        except Exception as e:
            logger.error("Voice cloning initialization failed: %s", e, exc_info=True)
            logger.warning("Falling back to macOS TTS")

    return _voice_cloner


async def text_to_speech(text: str) -> tuple[Path, str]:
    """
    Convert text to speech.

    Returns:
        (audio_path, media_type) tuple
    """
    cloner = _get_voice_cloner()

    if cloner:
        try:
            path = await asyncio.to_thread(cloner.synthesize_sync, text)
            return path, MEDIA_TYPE_WAV
        except Exception as e:
            logger.error("Voice cloning synthesis failed: %s", e)
            logger.warning("Falling back to macOS TTS")

    # Fallback: macOS say
    output_path = Path(tempfile.mktemp(suffix=".aiff"))
    await asyncio.to_thread(
        subprocess.run,
        ["say", "-v", MACOS_VOICE, "-o", str(output_path), text],
        check=True
    )
    return output_path, MEDIA_TYPE_AIFF
