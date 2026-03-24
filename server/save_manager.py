import json
import logging
import re
from pathlib import Path

from config import DEFAULT_SAVE_NAME

logger = logging.getLogger(__name__)

SAVES_DIR = Path(__file__).parent.parent / "saves"

_active_save: str = DEFAULT_SAVE_NAME


def sanitize_name(name: str) -> str:
    """Sanitize a save name from voice input into a valid directory name."""
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s]+", "-", name)
    name = name.strip("-")
    return name or DEFAULT_SAVE_NAME


def get_template_path() -> Path:
    return SAVES_DIR / "template" / "party.json"


def get_party_json_path() -> Path:
    return SAVES_DIR / _active_save / "party.json"


def get_active_save() -> str:
    return _active_save


def _ensure_save_exists(name: str) -> None:
    """Create a save directory with an empty party.json if it doesn't exist."""
    save_dir = SAVES_DIR / name
    party_path = save_dir / "party.json"
    if not party_path.exists():
        save_dir.mkdir(parents=True, exist_ok=True)
        with open(party_path, "w") as f:
            json.dump({"characters": {}}, f, indent=2)
        logger.info("Created new save '%s'", name)


def switch_save(name: str) -> str:
    """Switch to a save by name. Creates it from template if it doesn't exist."""
    global _active_save
    name = sanitize_name(name)
    _ensure_save_exists(name)
    _active_save = name
    logger.info("Switched to save '%s'", name)
    return f"Switched to save {name}."


def create_save(name: str) -> str:
    """Create a new save and switch to it."""
    global _active_save
    name = sanitize_name(name)
    save_dir = SAVES_DIR / name
    if save_dir.exists():
        _active_save = name
        return f"Save {name} already exists. Switched to it."
    _ensure_save_exists(name)
    _active_save = name
    logger.info("Created and switched to save '%s'", name)
    return f"Created save {name} and switched to it."


def update_party(characters: list[dict]) -> None:
    """Write extracted character data into the active save's party.json."""
    party_path = get_party_json_path()
    if party_path.exists():
        with open(party_path) as f:
            party = json.load(f)
    else:
        party = {"characters": {}}

    existing = party.get("characters", {})
    added = []

    for char in characters:
        name = char.get("name")
        if not name:
            continue
        char_data = {k: v for k, v in char.items() if k != "name"}
        existing[name] = char_data
        added.append(name)

    party["characters"] = existing

    with open(party_path, "w") as f:
        json.dump(party, f, indent=2, sort_keys=True)

    logger.info("Updated party.json with characters: %s", ", ".join(added))


def load_party_context() -> str:
    """Load the active party.json as a string for LLM context.

    Filters out the _template character. Returns empty string if no real characters.
    """
    party_path = get_party_json_path()
    if not party_path.exists():
        return ""

    with open(party_path) as f:
        party = json.load(f)

    characters = party.get("characters", {})
    if not characters:
        return ""

    return json.dumps({"characters": characters}, indent=2)


def get_decisions_path() -> Path:
    return SAVES_DIR / _active_save / "decisions.json"


def load_decisions_context() -> str:
    """Load the active save's decisions as a string for LLM context."""
    decisions_path = get_decisions_path()
    if not decisions_path.exists():
        return ""

    with open(decisions_path) as f:
        decisions = json.load(f)

    if not decisions:
        return ""

    return json.dumps(decisions, indent=2)


def add_decision(decision: dict) -> None:
    """Append a decision to the active save's decisions.json."""
    decisions_path = get_decisions_path()
    if decisions_path.exists():
        with open(decisions_path) as f:
            decisions = json.load(f)
    else:
        decisions = []

    decisions.append(decision)

    with open(decisions_path, "w") as f:
        json.dump(decisions, f, indent=2)

    logger.info("Recorded decision: %s", decision.get("decision", ""))


def list_saves() -> list[str]:
    """List all available save names, excluding the template."""
    if not SAVES_DIR.exists():
        return []
    return sorted(
        d.name
        for d in SAVES_DIR.iterdir()
        if d.is_dir() and d.name != "template"
    )
