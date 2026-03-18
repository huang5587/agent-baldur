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
    VOICE_CLONE_ENABLED,
    VOICE_CLONE_CHECKPOINT_DIR,
    VOICE_CLONE_REFERENCE_AUDIO,
    VOICE_CLONE_REFERENCE_TEXT,
)

logger = logging.getLogger(__name__)

MACOS_VOICE = "Moira"

# Lazy-loaded voice cloning state
_voice_cloner: "VoiceCloner | None" = None


class VoiceCloner:
    """Fish Audio voice cloning with pre-loaded models."""

    def __init__(self, checkpoint_dir: Path, reference_audio: Path, reference_text_path: Path):
        # Debug: check Python environment
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"sys.path: {sys.path[:3]}")

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
        logger.info(f"Loaded reference transcript: {self.reference_text[:50]}...")

        logger.info(f"Loading Fish Audio models on {self.device}...")

        # Pre-load models (cached in fish_tts_core)
        load_codec_model(checkpoint_dir, self.device)
        load_semantic_model(checkpoint_dir, self.device)

        # Pre-extract reference voice
        logger.info(f"Extracting voice from {reference_audio.name}...")
        self.reference_tokens = extract_reference_tokens(
            reference_audio, checkpoint_dir, self.device
        )

        logger.info("Voice cloning ready")

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

    if not VOICE_CLONE_ENABLED:
        return None

    if _voice_cloner is None:
        try:
            _voice_cloner = VoiceCloner(
                VOICE_CLONE_CHECKPOINT_DIR,
                VOICE_CLONE_REFERENCE_AUDIO,
                VOICE_CLONE_REFERENCE_TEXT
            )
        except Exception as e:
            import traceback
            logger.error(f"Voice cloning init failed: {e}")
            logger.error(traceback.format_exc())
            logger.warning("Falling back to macOS say")

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
            return path, "audio/wav"
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}, falling back to macOS say")

    # Fallback: macOS say
    output_path = Path(tempfile.mktemp(suffix=".aiff"))
    await asyncio.to_thread(
        subprocess.run,
        ["say", "-v", MACOS_VOICE, "-o", str(output_path), text],
        check=True
    )
    return output_path, "audio/aiff"
