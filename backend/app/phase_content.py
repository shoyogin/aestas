"""Canonical cycle-phase copy.

app/content/phase_panels.json is the single source of truth: the backend serves
it to the frontend at /content/phases, so the copy is never written twice.
Friend view = lite panels, no "drive". Partner view = full panels + support line.
"""
import json
from functools import lru_cache
from pathlib import Path

CONTENT_PATH = Path(__file__).parent / "content" / "phase_panels.json"


@lru_cache(maxsize=1)
def load_content() -> dict:
    """Read and cache the phase copy (the file never changes at runtime)."""
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def owner_content() -> dict:
    """Everything the logged-in user's own dashboard needs."""
    content = load_content()
    return {
        "labels": content["labels"],
        "panel_order": content["panel_order"],
        "panel_headings": content["panel_headings"],
        "panels": content["panels"],
        "disclaimer": content["disclaimer"],
    }


def panels_for_link(phase: str | None, link_type: str) -> dict | None:
    """The subset of the copy this follower is allowed to see."""
    if not phase:
        return None
    content = load_content()
    if link_type == "partner":
        panels = content["panels"].get(phase)
        if not panels:
            return None
        return {**panels, "support": content["partner_support"].get(phase)}
    lite = content["friend_lite"].get(phase)
    if not lite:
        return None
    return {**lite, "support": None}


def shared_disclaimer() -> str:
    return load_content()["shared_disclaimer"]
