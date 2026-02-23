from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
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

    def decide_next_action(self, context: str) -> str:
        # Placeholder for LLM routing logic
        # 1. Check boredom/curiosity
        # 2. If bored > 0.8, try something crazy (High temperature LLM call)
        # 3. If needs.survival < 0.3, focus on eating/gathering
        pass

    def update_state_after_action(self, action: str):
        # Update boredom, energy, needs based on action outcome
        pass
