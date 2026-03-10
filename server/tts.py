import subprocess
import tempfile
from pathlib import Path


async def text_to_speech(text: str) -> Path:
    output_path = Path(tempfile.mktemp(suffix=".aiff"))
    subprocess.run(
        ["say", "-o", str(output_path), text],
        check=True,
    )
    return output_path
