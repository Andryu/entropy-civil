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
class Belief:
    """A myth-derived belief that can steer future agent behavior."""

    kind: str
    text: str
    source_agent_id: str
    source_turn: int
    strength: float = 0.5
    trigger: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "text": self.text,
            "source_agent_id": self.source_agent_id,
            "source_turn": self.source_turn,
            "strength": self.strength,
            "trigger": self.trigger,
        }


@dataclass
class WorldState:
    """Mutable world state that makes agent actions affect civilization context."""

    weather: str
    resources: dict[str, int]
    locations: dict[str, Location] = field(default_factory=dict)
    beliefs: list[Belief] = field(default_factory=list)
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
            "beliefs": [belief.to_dict() for belief in self.beliefs[-25:]],
            "events": list(self.events[-25:]),
        }

    def add_beliefs(self, beliefs: list[Belief]) -> None:
        if not beliefs:
            return
        self.beliefs.extend(beliefs)
        self.beliefs = self.beliefs[-50:]


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


def derive_beliefs_from_reflection(
    agent_id: str,
    reflection: str,
    turn: int,
    rng: random.Random | None = None,
) -> list[Belief]:
    """Convert a mythic reflection into one or more belief candidates."""

    rng = rng or random.Random()
    lowered = reflection.lower()
    beliefs: list[Belief] = []

    def add_belief(kind: str, text: str, trigger: str, base_strength: float = 0.6) -> None:
        strength = min(1.0, base_strength + rng.uniform(0.0, 0.2))
        beliefs.append(
            Belief(
                kind=kind,
                text=text,
                source_agent_id=agent_id,
                source_turn=turn,
                strength=strength,
                trigger=trigger,
            )
        )

    if any(word in lowered for word in ["punished", "forbidden", "avoid", "curse", "never"]):
        if any(word in lowered for word in ["fish", "fishing", "river", "dawn"]):
            add_belief(
                "taboo",
                "Avoid fishing at dawn near the river.",
                "punishment around fishing at dawn",
            )

    if any(word in lowered for word in ["ritual", "chant", "humming", "dance", "offer"]):
        add_belief(
            "ritual",
            "The village should repeat the chant or ritual that kept the spirits calm.",
            "ritual language in the reflection",
        )

    if any(word in lowered for word in ["sacred", "holy", "spirit", "shrine"]):
        if any(word in lowered for word in ["river", "forest", "cave", "meadow", "fire"]):
            add_belief(
                "sacred_location",
                "A nearby place has become sacred and should be treated with care.",
                "sacred place language in the reflection",
            )

    if any(word in lowered for word in ["omen", "sign", "stars", "spiral", "moon"]):
        add_belief(
            "omen",
            "Signs in the sky warn the village to change its path.",
            "omen language in the reflection",
            base_strength=0.55,
        )

    if any(word in lowered for word in ["law", "rule", "must", "should", "custom"]):
        add_belief(
            "law",
            "The village has learned a rule worth following.",
            "law language in the reflection",
        )

    if any(word in lowered for word in ["will", "future", "one day", "spring", "return"]):
        add_belief(
            "prophecy",
            "The reflection points to a future event the village should prepare for.",
            "prophetic language in the reflection",
            base_strength=0.52,
        )

    if not beliefs and reflection.strip():
        add_belief(
            "omen",
            "The reflection feels like a sign worth remembering.",
            "fallback myth recognition",
            base_strength=0.4,
        )

    return beliefs


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
