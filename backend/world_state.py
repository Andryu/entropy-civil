from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Location:
    """A deterministic place in the sandbox civilization map."""

    id: str
    name: str
    x: float
    y: float
    biome: str
    resources: list[str]
    activity: int = 0
    last_event: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "biome": self.biome,
            "resources": list(self.resources),
            "activity": self.activity,
            "last_event": self.last_event,
        }


@dataclass
class WorldState:
    """Mutable world state that makes agent actions affect civilization context."""

    weather: str
    resources: dict[str, int]
    locations: dict[str, Location] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create_default(cls, rng: random.Random | None = None) -> "WorldState":
        rng = rng or random.Random()
        weather = rng.choice(["clear", "windy", "misty", "rainy"])
        return cls(
            weather=weather,
            resources={
                "food": 20,
                "wood": 12,
                "stone": 8,
                "fish": 6,
                "lore": 0,
            },
            locations={
                "river": Location("river", "Silver River", 18.0, 66.0, "water", ["fish", "food"]),
                "forest": Location("forest", "Deep Forest", 76.0, 30.0, "forest", ["wood", "food"]),
                "fire_pit": Location("fire_pit", "Central Fire Pit", 50.0, 52.0, "settlement", ["lore"]),
                "cave": Location("cave", "Echo Cave", 18.0, 22.0, "stone", ["stone", "lore"]),
                "meadow": Location("meadow", "Open Meadow", 72.0, 72.0, "grassland", ["food"]),
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "weather": self.weather,
            "resources": dict(self.resources),
            "locations": [location.to_dict() for location in self.locations.values()],
            "events": list(self.events[-25:]),
        }


def apply_agent_action_to_world(
    world: WorldState,
    agent_id: str,
    action: str,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    """Apply a simple deterministic resource/location effect from an agent action."""

    rng = rng or random.Random()
    lowered = action.lower()
    location_id = _infer_location_id(lowered)
    resource_id, effect = _infer_resource_effect(lowered)
    amount = rng.randint(1, 3)

    if effect == "increase":
        world.resources[resource_id] = world.resources.get(resource_id, 0) + amount
    elif effect == "decrease":
        world.resources[resource_id] = max(0, world.resources.get(resource_id, 0) - amount)
    else:
        amount = 0

    location = world.locations[location_id]
    location.activity += 1

    event = {
        "agent_id": agent_id,
        "location_id": location_id,
        "resource_id": resource_id,
        "effect": effect,
        "amount": amount,
        "description": _describe_world_event(agent_id, location_id, resource_id, effect, amount),
    }
    location.last_event = event["description"]
    world.events.append(event)
    return event


def _infer_location_id(action: str) -> str:
    location_keywords = [
        ("river", ["river", "fish", "fishing", "net"]),
        ("forest", ["forest", "deer", "feather", "wood", "tree"]),
        ("fire_pit", ["fire", "children", "shares", "humming", "ritual"]),
        ("cave", ["cave", "stone", "echo", "dark"]),
        ("meadow", ["berry", "berries", "grass", "meadow"]),
    ]
    for location_id, keywords in location_keywords:
        if any(keyword in action for keyword in keywords):
            return location_id
    return "fire_pit"


def _infer_resource_effect(action: str) -> tuple[str, str]:
    if any(word in action for word in ["gather", "berries", "food", "shares"]):
        return "food", "increase"
    if any(word in action for word in ["fish", "fishing", "net"]):
        return "fish", "increase"
    if any(word in action for word in ["wood", "repairs", "craft"]):
        return "wood", "decrease"
    if any(word in action for word in ["stone", "cave"]):
        return "stone", "increase"
    if any(word in action for word in ["tells", "hidden name", "stars", "spiral", "omen"]):
        return "lore", "increase"
    return "lore", "increase"


def _describe_world_event(agent_id: str, location_id: str, resource_id: str, effect: str, amount: int) -> str:
    verb = "changed"
    if effect == "increase":
        verb = "increased"
    elif effect == "decrease":
        verb = "consumed"
    return f"{agent_id} {verb} {resource_id} by {amount} at {location_id}."
