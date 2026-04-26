from __future__ import annotations

import random
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, List


@dataclass
class DemoMemoryItem:
    content: str
    importance: float
    timestamp: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entropy_level: float = 0.0


class DemoMemorySystem:
    """In-memory memory backend for deterministic demos and tests."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.short_term: List[DemoMemoryItem] = []

    def add_memory(self, content: str, importance: float, timestamp: int):
        self.short_term.append(
            DemoMemoryItem(content=content, importance=importance, timestamp=timestamp)
        )

    def reflect_and_summarize(self, current_time: int) -> List[DemoMemoryItem]:
        reflected = [mem for mem in self.short_term if mem.importance >= 0.5]
        self.short_term = []
        return reflected

    def retrieve_relevant(self, query: str, top_k: int = 5) -> list[Any]:
        return []


class DemoLLMRouter:
    """Deterministic LLM stand-in for local demos without Ollama."""

    def __init__(self, seed: int | None = None):
        self.random = random.Random(seed)
        self.actions = [
            "[DEMO] gathers bright berries near the river and shares them by the fire.",
            "[DEMO] sketches a spiral mark on a flat stone after watching the stars.",
            "[DEMO] follows deer tracks into the forest and returns with a strange feather.",
            "[DEMO] repairs a fishing net while humming an old rhythm.",
            "[DEMO] tells the children that the wind has a hidden name.",
        ]
        self.reflections = [
            "[DEMO] The villagers remember the river as generous and name it the Silver Mother.",
            "[DEMO] The spiral stone becomes an omen of safe return from the dark forest.",
            "[DEMO] The feather is said to belong to a sky spirit watching the village.",
        ]

    def chat_daily(self, prompt: str) -> str:
        agent_name = _extract_agent_name(prompt)
        action = self.random.choice(self.actions)
        return f"{agent_name} {action}"

    def reflect_and_hallucinate(self, memories: list[Any], entropy_factor: float) -> str:
        reflection = self.random.choice(self.reflections)
        memory_texts = []
        for memory in memories:
            if hasattr(memory, "content"):
                memory_texts.append(str(memory.content))
            elif isinstance(memory, str):
                memory_texts.append(memory)
        if memory_texts:
            return f"{reflection} Echo: {memory_texts[-1]}"
        return reflection

    def extract_vector(self, text: str) -> list[float]:
        return [self.random.uniform(-1, 1) for _ in range(3)]


def _extract_agent_name(prompt: str) -> str:
    match = re.search(r"Agent-\d+", prompt)
    return match.group(0) if match else "Agent"
