from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import re
import uuid


class Needs(BaseModel):
    survival: float = 1.0     # 0.0 to 1.0
    safety: float = 1.0
    belonging: float = 0.5
    esteem: float = 0.5
    self_actualization: float = 0.1


class AgentState(BaseModel):
    boredom: float = 0.0      # Increases when doing repeated actions
    curiosity: float = 1.0    # Drives seeking new knowledge/places
    energy: float = 1.0       # Decreases with actions
    needs: Needs = Field(default_factory=Needs)
    x: float = 50.0           # Sandbox X coordinate (0-100)
    y: float = 50.0           # Sandbox Y coordinate (0-100)
    emotion: str = "😐"        # Sandbox visual emotion
    current_action: str = "Idle" # Sandbox action text
    speech: str = ""          # Sandbox speech bubble


class AgentIdentity(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    personality: str          # e.g., "Curious and brave", "Cautious and traditional"
    skills: Dict[str, float] = Field(default_factory=dict) # e.g., {"farming": 0.2, "crafting": 0.1}


class Agent:
    def __init__(self, name: str, personality: str):
        self.identity = AgentIdentity(name=name, personality=personality)
        self.state = AgentState()
        self.memory = None # Will be injected
        self.brain: Optional[Any] = None
        self.relationships: Dict[str, float] = {}
        self.last_action: str = "Idle"

    def decide_next_action(self, context: str) -> str:
        prompt = self._build_action_prompt(context)
        if self.brain is not None and hasattr(self.brain, "chat_daily"):
            result = self.brain.chat_daily(prompt)
            if result and "[FALLBACK]" not in result:
                return result

        return self._heuristic_next_action(context)

    def update_state_after_action(self, action: str):
        lowered = action.lower()
        previous_action = self.last_action.lower()
        repeated = any(token in lowered and token in previous_action for token in ["gather", "fish", "explore", "talk", "rest", "craft", "share", "repair"])

        energy_delta = -0.05
        boredom_delta = 0.02

        if any(word in lowered for word in ["rest", "sleep", "recover", "nap"]):
            energy_delta = 0.16
            boredom_delta = -0.08
            self.state.needs.safety = min(1.0, self.state.needs.safety + 0.04)
        elif any(word in lowered for word in ["gather", "hunt", "fish", "eat", "food", "berries"]) and not any(word in lowered for word in ["share", "shares", "talk", "discuss", "help", "meet"]):
            energy_delta = 0.06 if "eat" in lowered else -0.03
            boredom_delta = -0.02
            self.state.needs.survival = min(1.0, self.state.needs.survival + 0.08)
        elif any(word in lowered for word in ["talk", "discuss", "share", "shares", "help", "meet"]):
            energy_delta = -0.04
            boredom_delta = -0.12
            self.state.needs.belonging = min(1.0, self.state.needs.belonging + 0.12)
            self.state.needs.esteem = min(1.0, self.state.needs.esteem + 0.03)
        elif any(word in lowered for word in ["explore", "discover", "wander", "search", "travel"]):
            energy_delta = -0.08
            boredom_delta = -0.14
            self.state.curiosity = min(1.0, self.state.curiosity + 0.06)
        elif any(word in lowered for word in ["craft", "repair", "build", "make"]):
            energy_delta = -0.07
            boredom_delta = -0.04
            self.state.needs.esteem = min(1.0, self.state.needs.esteem + 0.1)
            self.state.needs.self_actualization = min(1.0, self.state.needs.self_actualization + 0.04)

        if repeated:
            boredom_delta += 0.08

        self.state.energy = _clamp(self.state.energy + energy_delta)
        self.state.boredom = _clamp(self.state.boredom + boredom_delta)
        self.state.needs.survival = _clamp(self.state.needs.survival)
        self.state.needs.safety = _clamp(self.state.needs.safety)
        self.state.needs.belonging = _clamp(self.state.needs.belonging)
        self.state.needs.esteem = _clamp(self.state.needs.esteem)
        self.state.needs.self_actualization = _clamp(self.state.needs.self_actualization)

        for other_agent_id, strength in list(self.relationships.items()):
            if not re.search(rf"\b{re.escape(other_agent_id)}\b", action):
                continue
            if any(word in lowered for word in ["share", "shares", "talk", "help", "gift", "listen", "meet"]):
                strength += 0.1
            elif any(word in lowered for word in ["argue", "fight", "insult", "steal", "blame"]):
                strength -= 0.15
            else:
                strength += 0.02
            self.relationships[other_agent_id] = _clamp_relationship(strength)

        self.state.current_action = action
        self.last_action = action
        return None

    def _build_action_prompt(self, context: str) -> str:
        relationship_lines = self._relationship_lines()
        relationship_section = "\n".join(relationship_lines) if relationship_lines else "- none yet"
        needs = self.state.needs
        return (
            f"You are {self.identity.name}, a {self.identity.personality}.\n"
            f"Current context: {context}\n\n"
            f"State:\n"
            f"- energy: {self.state.energy:.2f}\n"
            f"- boredom: {self.state.boredom:.2f}\n"
            f"- curiosity: {self.state.curiosity:.2f}\n"
            f"- needs: survival={needs.survival:.2f}, safety={needs.safety:.2f}, belonging={needs.belonging:.2f}, esteem={needs.esteem:.2f}, self_actualization={needs.self_actualization:.2f}\n\n"
            f"Relationship context:\n{relationship_section}\n\n"
            "Choose one short action (1-2 sentences) that fits the current state."
        )

    def _relationship_lines(self) -> list[str]:
        lines = []
        for other_agent_id, strength in sorted(self.relationships.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- {other_agent_id}: trust {strength:+.2f}")
        return lines

    def _heuristic_next_action(self, context: str) -> str:
        strongest_relationship = max(self.relationships.values(), default=0.0)
        lowered_context = context.lower()

        if any(word in lowered_context for word in ["taboo", "forbidden", "avoid fishing", "river taboo"]) and any(
            word in lowered_context for word in ["fish", "fishing", "river", "dawn"]
        ):
            if self.state.needs.survival < 0.35:
                partner = self._best_relationship_target(prefer_positive=True)
                if partner:
                    return f"{self.identity.name} gathers berries in the meadow with {partner}, honoring the taboo."
                return f"{self.identity.name} gathers berries in the meadow, honoring the taboo."
            return f"{self.identity.name} gathers berries in the meadow instead of fishing at dawn."

        if self.state.needs.survival < 0.35:
            if strongest_relationship > 0.4:
                partner = self._best_relationship_target(prefer_positive=True)
                if partner:
                    return f"{self.identity.name} gathers food with {partner} near the river."
            return f"{self.identity.name} gathers food near the river."

        if self.state.boredom > 0.8 or self.state.curiosity > 0.85:
            if strongest_relationship > 0.3:
                partner = self._best_relationship_target(prefer_positive=True)
                if partner:
                    return f"{self.identity.name} explores a new path with {partner} beyond the meadow."
            return f"{self.identity.name} explores the forest for something new."

        if self.state.needs.belonging < 0.45 or strongest_relationship > 0.6:
            partner = self._best_relationship_target(prefer_positive=True)
            if partner:
                return f"{self.identity.name} shares a story with {partner} by the fire."
            return f"{self.identity.name} talks with neighbors by the fire."

        if self.state.energy < 0.35:
            return f"{self.identity.name} rests by the fire to recover energy."

        if any(word in lowered_context for word in ["storm", "winter", "hunger", "empty"]):
            return f"{self.identity.name} checks the stores and gathers food near the river."

        if any(word in lowered_context for word in ["prophecy", "omen", "sacred_location"]):
            return f"{self.identity.name} visits the fire pit to listen for the meaning of the omen."

        return f"{self.identity.name} crafts a small tool and reflects on the day."

    def _best_relationship_target(self, prefer_positive: bool = True) -> Optional[str]:
        if not self.relationships:
            return None
        items = sorted(self.relationships.items(), key=lambda item: item[1], reverse=prefer_positive)
        for agent_id, strength in items:
            if prefer_positive and strength <= 0:
                continue
            return agent_id
        return items[0][0] if items else None


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _clamp_relationship(value: float) -> float:
    return max(-1.0, min(1.0, value))
