from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Optional


def build_structured_event_data(
    *,
    event_type: str,
    agent_id: str,
    content: str,
    turn: int,
    location_id: Optional[str] = None,
    target: Optional[str] = None,
    cause: Optional[str] = None,
    effect: Optional[str] = None,
    world_event: Optional[Dict[str, Any]] = None,
    importance: float = 0.5,
    entropy_level: float = 0.0,
    causal_parent_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a JSON-serializable structured event payload."""

    world_event = world_event or {}
    action = _infer_action(event_type, content, world_event)
    inferred_target = target or _infer_target(content)
    inferred_location = location_id or world_event.get("location_id") or _infer_location(content, world_event)
    inferred_cause = cause or _infer_cause(event_type, content, world_event)
    inferred_effect = effect or _infer_effect(event_type, content, world_event)
    tags = _build_tags(event_type, action, inferred_location, world_event, content)
    return {
        "actor": agent_id,
        "action": action,
        "target": inferred_target,
        "location": inferred_location,
        "cause": inferred_cause,
        "effect": inferred_effect,
        "outcome": _infer_outcome(event_type, content, world_event),
        "tags": tags,
        "importance": importance,
        "entropy_level": entropy_level,
        "causal_parent_id": causal_parent_id,
        "turn": turn,
        "event_type": event_type,
        "content": content,
    }


def simulation_event_to_dict(event_row: Any) -> Dict[str, Any]:
    """Flatten a SimulationEvent row/dict for API responses."""

    if isinstance(event_row, dict):
        base = dict(event_row)
    else:
        base = {
            "id": getattr(event_row, "id", None),
            "turn": getattr(event_row, "turn", None),
            "agent_id": getattr(event_row, "agent_id", None),
            "event_type": getattr(event_row, "event_type", None),
            "content": getattr(event_row, "content", None),
            "structured_data": getattr(event_row, "structured_data", None),
            "created_at": getattr(event_row, "created_at", None),
        }

    structured = base.get("structured_data") or {}
    payload = {
        "id": base.get("id"),
        "turn": base.get("turn"),
        "agent_id": base.get("agent_id"),
        "type": base.get("event_type"),
        "content": base.get("content"),
        "structured": structured,
    }

    payload.update(
        {
            "actor": structured.get("actor"),
            "action": structured.get("action"),
            "target": structured.get("target"),
            "location": structured.get("location"),
            "cause": structured.get("cause"),
            "effect": structured.get("effect"),
            "tags": structured.get("tags", []),
            "importance": structured.get("importance"),
            "entropy_level": structured.get("entropy_level"),
            "causal_parent_id": structured.get("causal_parent_id"),
        }
    )
    return payload


def _infer_action(event_type: str, content: str, world_event: Dict[str, Any]) -> str:
    lowered = content.lower()
    if event_type == "REFLECTION":
        return "reflect"
    if "shares" in lowered or "share" in lowered:
        return "share"
    if any(word in lowered for word in ["gather", "gathers", "hunt", "fish", "forage"]):
        return "gather"
    if any(word in lowered for word in ["explore", "explores", "wander", "travel", "discover"]):
        return "explore"
    if any(word in lowered for word in ["rest", "sleep", "recover", "nap"]):
        return "rest"
    if any(word in lowered for word in ["craft", "repair", "build", "make"]):
        return "craft"
    if any(word in lowered for word in ["talk", "discuss", "meet", "listen", "help"]):
        return "socialize"
    if world_event.get("resource_id"):
        return str(world_event["resource_id"])
    return "act"


def _infer_target(content: str) -> Optional[str]:
    matches = re.findall(r"\b[A-Z][A-Za-z0-9_-]*-\d+\b", content)
    return matches[0] if matches else None


def _infer_location(content: str, world_event: Dict[str, Any]) -> Optional[str]:
    lowered = content.lower()
    if world_event.get("location_id"):
        return str(world_event["location_id"])
    for location_id, keywords in (
        ("river", ["river", "fish", "fishing", "water"]),
        ("forest", ["forest", "wood", "tree", "deer"]),
        ("fire_pit", ["fire", "council", "story", "share", "ritual"]),
        ("cave", ["cave", "stone", "echo", "dark"]),
        ("meadow", ["meadow", "berry", "berries", "grass"]),
    ):
        if any(keyword in lowered for keyword in keywords):
            return location_id
    return None


def _infer_cause(event_type: str, content: str, world_event: Dict[str, Any]) -> str:
    if event_type == "REFLECTION":
        return "memory consolidation"
    resource_id = world_event.get("resource_id")
    if resource_id:
        return f"resource {resource_id} activity"
    return "agent decision"


def _infer_effect(event_type: str, content: str, world_event: Dict[str, Any]) -> str:
    if event_type == "REFLECTION":
        return "myth or belief update"
    effect = world_event.get("effect")
    if effect:
        return str(effect)
    return "changed"


def _infer_outcome(event_type: str, content: str, world_event: Dict[str, Any]) -> str:
    if event_type == "REFLECTION":
        return "mythic memory synthesized"
    resource_id = world_event.get("resource_id")
    amount = world_event.get("amount")
    effect = world_event.get("effect")
    if resource_id and amount is not None and effect:
        sign = "+" if effect == "increase" else "-"
        return f"{resource_id} {sign}{amount}"
    return "state changed"


def _build_tags(
    event_type: str,
    action: str,
    location_id: Optional[str],
    world_event: Dict[str, Any],
    content: str,
) -> list[str]:
    tags = {event_type.lower(), action}
    if location_id:
        tags.add(f"location:{location_id}")
    resource_id = world_event.get("resource_id")
    if resource_id:
        tags.add(f"resource:{resource_id}")
    lowered = content.lower()
    for keyword, tag in (
        ("taboo", "myth:taboo"),
        ("ritual", "myth:ritual"),
        ("spirit", "myth:spirit"),
        ("omen", "myth:omen"),
        ("prophecy", "myth:prophecy"),
        ("law", "myth:law"),
        ("council", "social:council"),
        ("share", "social:share"),
    ):
        if keyword in lowered:
            tags.add(tag)
            if tag.startswith("myth:"):
                tags.add("myth")
    return sorted(tags)
