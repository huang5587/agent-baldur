import subprocess
import tempfile
from pathlib import Path

# Change this to any voice from: say -v '?'
# Examples: "Samantha", "Daniel", "Karen", "Moira", "Rishi"
TTS_VOICE = "Moira"


async def text_to_speech(text: str) -> Path:
    output_path = Path(tempfile.mktemp(suffix=".aiff"))
    subprocess.run(
        ["say", "-v", TTS_VOICE, "-o", str(output_path), text],
        check=True,
    )
    return output_path
