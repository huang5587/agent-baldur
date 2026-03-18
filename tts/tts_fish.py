#!/usr/bin/env python3
"""
Fish Audio S1-Mini TTS - CLI Tool

This script uses the Fish Audio S1-mini model for text-to-speech generation.
Model: https://huggingface.co/fishaudio/s1-mini

Requirements:
    pip install fish-speech torchcodec soundfile
    # Or for CUDA GPU support:
    pip install fish-speech[cu129] torchcodec soundfile

Platforms:
    - CUDA: Full support (24GB VRAM recommended)
    - MPS (Apple Silicon): Supported, auto-detected
    - CPU: Supported but slow

Setup:
    1. Accept the model terms at https://huggingface.co/fishaudio/s1-mini
    2. Login to HuggingFace: huggingface-cli login
    3. Download model: huggingface-cli download fishaudio/s1-mini --local-dir checkpoints/s1-mini
"""

import argparse
import subprocess
import sys
from pathlib import Path

from fish_tts_core import (
    DEFAULT_CHECKPOINT_DIR,
    get_device,
    extract_reference_tokens,
    synthesize,
)

# Default paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import torch
        import fish_speech
        import soundfile
        import torchaudio

        device = get_device()
        print(f"PyTorch version: {torch.__version__}")
        print(f"Available device: {device}")
        if device == "mps":
            print("  MPS (Apple Silicon) detected - avoid --compile flag")
        elif device == "cuda":
            print(f"  CUDA device: {torch.cuda.get_device_name(0)}")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nInstall fish-speech:")
        print("  pip install fish-speech torchcodec soundfile   # CPU/MPS")
        print("  pip install fish-speech[cu129] torchcodec soundfile  # CUDA GPU")
        return False


def download_model(checkpoint_dir: Path):
    """Download the s1-mini model from HuggingFace."""
    if checkpoint_dir.exists() and any(checkpoint_dir.iterdir()):
        print(f"Model already exists at {checkpoint_dir}")
        return True

    print("Downloading fishaudio/s1-mini model...")
    print("Note: You must first accept the model terms at https://huggingface.co/fishaudio/s1-mini")

    checkpoint_dir.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run([
        "huggingface-cli", "download",
        "fishaudio/s1-mini",
        "--local-dir", str(checkpoint_dir)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Download failed: {result.stderr}")
        print("\nMake sure you have:")
        print("  1. Accepted model terms at https://huggingface.co/fishaudio/s1-mini")
        print("  2. Logged in: huggingface-cli login")
        return False

    print("Model downloaded successfully!")
    return True


def text_to_speech(
    text: str,
    output_path: Path,
    reference_audio: Path = None,
    reference_text: str = None,
    checkpoint_dir: Path = None,
    emotion: str = None,
    tone: str = None,
    device: str = None
) -> Path:
    """
    Convert text to speech using Fish Audio S1-mini.

    Args:
        text: Text to convert to speech
        output_path: Output audio file path
        reference_audio: Optional reference audio for voice cloning
        reference_text: Optional transcript of reference audio
        checkpoint_dir: Path to model checkpoints
        emotion: Emotion marker (e.g., "excited", "sad", "angry")
        tone: Tone marker (e.g., "whispering", "shouting")
        device: Compute device (cuda, mps, cpu) - auto-detected if None

    Returns:
        Path to generated audio file

    Supported emotions: angry, sad, disdainful, excited, surprised, satisfied,
                       unhappy, anxious, hysterical, delighted, scared, worried,
                       joyful, confident, sincere, sarcastic

    Supported tones: (in a hurry tone), (shouting), (screaming), (whispering), (soft tone)

    Special markers: (laughing), (chuckling), (sobbing), (crying loudly), (sighing)
    """
    checkpoint_dir = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
    device = device or get_device()

    # Apply emotion/tone markers to text
    if emotion:
        text = f"[{emotion}] {text}"
    if tone:
        text = f"({tone}) {text}"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    reference_tokens = None

    # Extract reference tokens if reference audio provided
    if reference_audio:
        reference_audio = Path(reference_audio)
        if not reference_audio.exists():
            raise FileNotFoundError(f"Reference audio not found: {reference_audio}")

        print(f"Extracting voice features from {reference_audio}...")
        reference_tokens = extract_reference_tokens(
            reference_audio,
            checkpoint_dir,
            device=device
        )

    # Full TTS pipeline using core library
    print(f"Generating speech for: {text[:50]}...")
    synthesize(
        text=text,
        reference_tokens=reference_tokens,
        reference_text=reference_text,
        output_path=output_path,
        checkpoint_dir=checkpoint_dir,
        device=device
    )

    print(f"Audio saved to: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Fish Audio S1-mini Text-to-Speech",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic TTS
  python tts_fish.py "Hello, world!" -o output.wav

  # Use MPS (Apple Silicon)
  python tts_fish.py "Hello, world!" -o output.wav --device mps

  # Voice cloning with reference audio
  python tts_fish.py "Hello, world!" -o output.wav -r reference.wav -rt "Reference transcript"

  # With emotion
  python tts_fish.py "I can't believe it!" -o output.wav --emotion excited

  # With tone
  python tts_fish.py "This is a secret" -o output.wav --tone whispering

  # Check available device
  python tts_fish.py --check-deps

  # Download model
  python tts_fish.py --download-model
        """
    )

    parser.add_argument("text", nargs="?", help="Text to convert to speech")
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_DIR / "output.wav",
                        help="Output audio file path")
    parser.add_argument("-r", "--reference", type=Path,
                        help="Reference audio for voice cloning (10-30 seconds)")
    parser.add_argument("-rt", "--reference-text", type=str,
                        help="Transcript of reference audio")
    parser.add_argument("--checkpoint-dir", type=Path, default=DEFAULT_CHECKPOINT_DIR,
                        help="Path to model checkpoints")
    parser.add_argument("--emotion", type=str,
                        help="Emotion: excited, sad, angry, happy, etc.")
    parser.add_argument("--tone", type=str,
                        help="Tone: whispering, shouting, soft tone, etc.")
    parser.add_argument("--device", type=str, choices=["cuda", "mps", "cpu"],
                        help="Compute device (auto-detected if not specified)")
    parser.add_argument("--download-model", action="store_true",
                        help="Download the s1-mini model")
    parser.add_argument("--check-deps", action="store_true",
                        help="Check if dependencies are installed")

    args = parser.parse_args()

    if args.check_deps:
        if check_dependencies():
            print("All dependencies installed!")
        sys.exit(0)

    if args.download_model:
        success = download_model(args.checkpoint_dir)
        sys.exit(0 if success else 1)

    if not args.text:
        parser.print_help()
        sys.exit(1)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Auto-detect device if not specified
    device = args.device or get_device()
    print(f"Using device: {device}")

    try:
        text_to_speech(
            text=args.text,
            output_path=args.output,
            reference_audio=args.reference,
            reference_text=args.reference_text,
            checkpoint_dir=args.checkpoint_dir,
            emotion=args.emotion,
            tone=args.tone,
            device=device
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
