"""
Fish Audio S1-Mini Core Library

Shared model loading and inference functions.
Used by both CLI (tts_fish.py) and server (server/tts.py).

Models are loaded once and cached at module level for reuse.
"""

import tempfile
from pathlib import Path
from typing import Optional

import numpy as np

# Paths
SCRIPT_DIR = Path(__file__).parent
DEFAULT_CHECKPOINT_DIR = SCRIPT_DIR / "checkpoints" / "s1-mini"
DEFAULT_REFERENCE_AUDIO = SCRIPT_DIR / "examples" / "ian_speech_clip.mp3"

# Cached models (module-level singletons)
_codec_model = None
_semantic_model = None
_decode_one_token = None
_device = None


def get_device() -> str:
    """Detect best available compute device."""
    global _device
    if _device is None:
        try:
            import torch
            if torch.cuda.is_available():
                _device = "cuda"
            elif torch.backends.mps.is_available():
                _device = "mps"
            else:
                _device = "cpu"
        except ImportError:
            _device = "cpu"
    return _device


def get_precision(device: str):
    """Get appropriate precision for device."""
    import torch
    if device == "cuda":
        return torch.bfloat16
    elif device == "mps":
        return torch.float32
    else:
        return torch.float32


def load_codec_model(checkpoint_dir: Path = None, device: str = None):
    """Load and cache the audio codec model."""
    global _codec_model
    if _codec_model is None:
        from fish_speech.models.dac.inference import load_model
        checkpoint_dir = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
        device = device or get_device()
        _codec_model = load_model(
            "modded_dac_vq",
            str(checkpoint_dir / "codec.pth"),
            device
        )
    return _codec_model


def load_semantic_model(checkpoint_dir: Path = None, device: str = None):
    """Load and cache the text-to-semantic model."""
    global _semantic_model, _decode_one_token
    if _semantic_model is None:
        from fish_speech.models.text2semantic.inference import init_model
        checkpoint_dir = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
        device = device or get_device()
        precision = get_precision(device)
        _semantic_model, _decode_one_token = init_model(
            str(checkpoint_dir), device, precision
        )
    return _semantic_model, _decode_one_token


def extract_reference_tokens(
    reference_audio: Path,
    checkpoint_dir: Path = None,
    device: str = None
) -> np.ndarray:
    """
    Extract voice tokens from reference audio for cloning.

    Returns numpy array of shape [num_codebooks, seq_len].
    """
    import torch
    import torchaudio

    device = device or get_device()
    checkpoint_dir = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
    model = load_codec_model(checkpoint_dir, device)

    audio, sr = torchaudio.load(str(reference_audio))
    if sr != model.sample_rate:
        audio = torchaudio.functional.resample(audio, sr, model.sample_rate)

    # Convert to mono and add batch dimension
    audio = audio.mean(dim=0, keepdim=True).unsqueeze(0).to(device)

    with torch.no_grad():
        result = model.encode(audio)
        indices = result[0] if isinstance(result, tuple) else result

    return indices.squeeze(0).cpu().numpy()


def generate_semantic_tokens(
    text: str,
    prompt_tokens: np.ndarray = None,
    prompt_text: str = None,
    checkpoint_dir: Path = None,
    device: str = None
) -> np.ndarray:
    """
    Generate semantic tokens from text using cached model.

    Args:
        text: Text to convert to speech
        prompt_tokens: Pre-extracted voice tokens for cloning
        prompt_text: Transcript of reference audio (improves quality)
        checkpoint_dir: Model checkpoint directory
        device: Compute device (cuda/mps/cpu)

    Returns:
        numpy array of semantic tokens
    """
    import torch
    from fish_speech.models.text2semantic.inference import generate_long

    device = device or get_device()
    checkpoint_dir = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
    model, decode_one_token = load_semantic_model(checkpoint_dir, device)

    # Convert prompt_tokens to torch.Tensor if provided
    prompt_tokens_tensor = None
    if prompt_tokens is not None:
        prompt_tokens_tensor = torch.from_numpy(prompt_tokens).to(device)

    # generate_long is a generator, collect the codes
    codes = None
    for response in generate_long(
        model=model,
        device=device,
        decode_one_token=decode_one_token,
        text=text,
        prompt_tokens=prompt_tokens_tensor,
        prompt_text=prompt_text,
    ):
        if response.action == "sample" and response.codes is not None:
            codes = response.codes.cpu().numpy()
        elif response.action == "next":
            break

    return codes


def decode_to_audio(
    semantic_tokens: np.ndarray,
    checkpoint_dir: Path = None,
    device: str = None
) -> tuple[np.ndarray, int]:
    """
    Decode semantic tokens to audio waveform.

    Returns:
        (audio_samples, sample_rate) tuple
    """
    import torch

    device = device or get_device()
    checkpoint_dir = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
    model = load_codec_model(checkpoint_dir, device)

    codes = torch.from_numpy(semantic_tokens).to(device)
    if codes.dim() == 2:
        codes = codes.unsqueeze(0)

    feature_lengths = torch.tensor([semantic_tokens.shape[-1]], device=device)

    with torch.no_grad():
        result = model.decode(codes, feature_lengths)
        audio = result[0] if isinstance(result, tuple) else result

    return audio.squeeze().cpu().numpy(), model.sample_rate


def synthesize(
    text: str,
    reference_tokens: np.ndarray = None,
    reference_text: str = None,
    output_path: Path = None,
    checkpoint_dir: Path = None,
    device: str = None
) -> Path:
    """
    Full TTS pipeline: text -> semantic tokens -> audio.

    Args:
        text: Text to synthesize
        reference_tokens: Pre-extracted voice tokens for cloning
        reference_text: Transcript of reference audio (improves quality)
        output_path: Where to save audio (default: temp file)
        checkpoint_dir: Model checkpoint directory
        device: Compute device (cuda/mps/cpu)

    Returns:
        Path to generated WAV file
    """
    import soundfile as sf

    if output_path is None:
        output_path = Path(tempfile.mktemp(suffix=".wav"))

    checkpoint_dir = checkpoint_dir or DEFAULT_CHECKPOINT_DIR
    device = device or get_device()

    # Generate semantic tokens
    semantic = generate_semantic_tokens(
        text=text,
        prompt_tokens=reference_tokens,
        prompt_text=reference_text,
        checkpoint_dir=checkpoint_dir,
        device=device
    )

    # Decode to audio
    audio, sample_rate = decode_to_audio(
        semantic_tokens=semantic,
        checkpoint_dir=checkpoint_dir,
        device=device
    )

    # Save
    sf.write(str(output_path), audio, sample_rate)
    return output_path
