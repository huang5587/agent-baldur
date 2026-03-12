import json
import base64
from pathlib import Path
import httpx
from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    VISION_MODEL,
    CHARACTER_EXTRACTION_PROMPT_TEMPLATE,
    PARTY_JSON_PATH,
    PARTY_UPDATE_KEYWORDS,
)


def is_party_update_request(question: str) -> bool:
    """Check if the user's question is a party update request."""
    question_lower = question.lower()
    return any(keyword in question_lower for keyword in PARTY_UPDATE_KEYWORDS)


def _get_character_schema() -> str:
    """Read party.json and extract the character template as a schema."""
    party_path = Path(__file__).parent / PARTY_JSON_PATH

    with open(party_path) as f:
        party = json.load(f)

    # Get the template character (first key in characters dict)
    characters = party.get("characters", {})
    if not characters:
        raise ValueError("No character template found in party.json")

    template_name = next(iter(characters.keys()))
    template = characters[template_name]

    # Add "name" field since it's stored as the key
    schema = {"name": "string (character name)", **template}

    # Convert to formatted JSON with type hints
    return _add_type_hints(schema)


def _add_type_hints(obj, indent=0) -> str:
    """Convert a template object to a schema string with type hints."""
    spaces = "  " * indent

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = ["{"]
        items = list(obj.items())
        for i, (key, value) in enumerate(items):
            comma = "," if i < len(items) - 1 else ""
            hint = _add_type_hints(value, indent + 1)
            lines.append(f'{spaces}  "{key}": {hint}{comma}')
        lines.append(f"{spaces}}}")
        return "\n".join(lines)
    elif isinstance(obj, list):
        return '["..."]'
    elif isinstance(obj, bool):
        return "boolean"
    elif isinstance(obj, int):
        return "number"
    elif isinstance(obj, float):
        return "number"
    elif isinstance(obj, str):
        return '"string"' if obj == "" else f'"{obj}"'
    elif obj is None:
        return "null"
    else:
        return str(obj)


def _build_extraction_prompt() -> str:
    """Build the character extraction prompt using the schema from party.json."""
    schema = _get_character_schema()
    return CHARACTER_EXTRACTION_PROMPT_TEMPLATE.format(schema=schema)


async def extract_character_data(image_bytes: bytes) -> list[dict]:
    """Extract all party members from a screenshot. Returns a list of character dicts."""
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = _build_extraction_prompt()

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        },
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": VISION_MODEL,
                "messages": messages,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # Parse the JSON response
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        result = json.loads(content)
        # Ensure we always return a list
        if isinstance(result, dict):
            return [result]
        return result
