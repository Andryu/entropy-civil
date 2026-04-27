from __future__ import annotations

import argparse
import json
import os
import random
import time
from typing import Optional

from agent import Agent
from demo_runtime import DemoLLMRouter, DemoMemorySystem
from sandbox_utils import parse_agent_action
from world_state import WorldState, apply_agent_action_to_world, derive_beliefs_from_reflection


class Simulation:
    def __init__(self, num_agents: int = 5, demo_mode: bool = False, seed: Optional[int] = None):
        self.demo_mode = demo_mode
        self.random = random.Random(seed)
        self.world = WorldState.create_default(self.random)
        self.agent_locations: dict[str, str] = {}
        self.demo_events = []
        self._models = None
        self._SessionLocal = None
        self._detect_and_record_epoch = None
        self._generate_chronicle = None

        if demo_mode:
            self.router = DemoLLMRouter(seed=seed)
            memory_factory = DemoMemorySystem
            print(f"[Simulation] Starting demo mode with seed={seed}.")
        else:
            from database import SessionLocal, engine, Base
            from epoch_detector import detect_and_record_epoch
            from chronicle_summarizer import generate_chronicle
            from llm_router import LLMRouter
            from memory import MemorySystem
            import models

            # Ensure tables are created only for real DB-backed runs.
            Base.metadata.create_all(bind=engine)
            self._SessionLocal = SessionLocal
            self._models = models
            self._detect_and_record_epoch = detect_and_record_epoch
            self._generate_chronicle = generate_chronicle
            self.router = LLMRouter()
            memory_factory = MemorySystem

        self.agents = [Agent(f"Agent-{i}", "Curious pioneer") for i in range(num_agents)]
        if demo_mode:
            for i, agent in enumerate(self.agents):
                agent.identity.agent_id = f"demo-agent-{i}"

        # Seed simple relationship graph so social context can influence prompts and state.
        for agent in self.agents:
            agent.relationships = {
                other.identity.agent_id: 0.0
                for other in self.agents
                if other.identity.agent_id != agent.identity.agent_id
            }
            agent.brain = self.router

        # Inject memory system into agents
        for a in self.agents:
            a.memory = memory_factory(agent_id=a.identity.agent_id)

        self.turn = 0 if demo_mode else self._resume_turn()
        print(f"[Simulation] Resuming from turn {self.turn}.")

    def _resume_turn(self) -> int:
        """Read the last persisted turn from the DB to enable seamless restart."""
        if self.demo_mode or self._SessionLocal is None or self._models is None:
            return 0

        db = self._SessionLocal()
        try:
            last_event = db.query(self._models.SimulationEvent).order_by(
                self._models.SimulationEvent.turn.desc()
            ).first()
            if last_event:
                return int(last_event.turn) + 1
            return 0
        except Exception as e:
            print(f"[Simulation] Could not resume turn from DB: {e}. Starting from 0.")
            return 0
        finally:
            db.close()

    def step(self):
        """Execute one full turn in the simulation (e.g., 1 Day)"""
        print(f"--- Turn {self.turn} ---")

        if self.demo_mode:
            self._step_without_db()
        else:
            self._step_with_db()

        # Output current state for Sandbox View
        self._dump_sandbox_state()

        self.turn += 1

    def _step_without_db(self):
        for agent in self.agents:
            action = self._run_daily_action(agent)
            if action:
                self.demo_events.append({
                    "turn": self.turn,
                    "agent_id": agent.identity.agent_id,
                    "event_type": "DAILY_ACTION",
                    "content": action,
                })

        if self.turn % 5 == 0 and self.turn > 0:
            print(">>> The agents are reflecting... (Entropy Injection)")
            for agent in self.agents:
                reflection = self._run_reflection(agent)
                if reflection:
                    self.demo_events.append({
                        "turn": self.turn,
                        "agent_id": agent.identity.agent_id,
                        "event_type": "REFLECTION",
                        "content": reflection,
                    })

    def _step_with_db(self):
        db = self._SessionLocal()
        try:
            for agent in self.agents:
                action = self._run_daily_action(agent)
                if not action:
                    continue

                event = self._models.SimulationEvent(
                    turn=self.turn,
                    agent_id=agent.identity.agent_id,
                    event_type="DAILY_ACTION",
                    content=action,
                )
                db.add(event)

            if self.turn % 5 == 0 and self.turn > 0:
                print(">>> The agents are reflecting... (Entropy Injection)")
                for agent in self.agents:
                    reflection = self._run_reflection(agent)
                    if not reflection:
                        continue

                    event = self._models.SimulationEvent(
                        turn=self.turn,
                        agent_id=agent.identity.agent_id,
                        event_type="REFLECTION",
                        content=reflection,
                    )
                    db.add(event)

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Turn {self.turn} failed: {e}")
        finally:
            db.close()

        # Phase 5: Auto-detect and record new epochs every N turns
        self._detect_and_record_epoch(self.turn)

        # Phase 5: Generate chronicle summary every 100 turns
        self._generate_chronicle(self.turn)

    def _run_daily_action(self, agent: Agent) -> str | None:
        context = self._build_agent_context(agent)
        action = agent.decide_next_action(context)

        if not action or "[FALLBACK]" in action:
            print(f"[WARN] Agent {agent.identity.name} got a fallback response at turn {self.turn}. Skipping save.")
            return None

        agent.memory.add_memory(action, importance=0.5, timestamp=self.turn)
        world_event = apply_agent_action_to_world(
            self.world,
            agent.identity.agent_id,
            action,
            self.random,
        )
        self.agent_locations[agent.identity.agent_id] = world_event["location_id"]
        agent.update_state_after_action(action)

        # --- Sandbox State Update ---
        parsed = parse_agent_action(action)
        agent.state.emotion = parsed["emotion"]
        agent.state.current_action = parsed["action"]
        agent.state.speech = parsed["speech"]
        # Move toward the location affected by this action; seeded RNG keeps demo mode reproducible.
        location = self.world.locations[world_event["location_id"]]
        agent.state.x = max(0.0, min(100.0, location.x + self.random.uniform(-5.0, 5.0)))
        agent.state.y = max(0.0, min(100.0, location.y + self.random.uniform(-5.0, 5.0)))
        return action

    def _build_agent_context(self, agent: Agent) -> str:
        location_id = self.agent_locations.get(agent.identity.agent_id)
        if location_id and location_id in self.world.locations:
            location = self.world.locations[location_id]
            location_text = f"{location.name} ({location.biome}) at ({location.x:.1f}, {location.y:.1f})"
        else:
            location_text = "unknown location"

        resource_bits = ", ".join(f"{name}={amount}" for name, amount in sorted(self.world.resources.items()))
        relationship_bits = ", ".join(
            f"{other}:{strength:+.2f}"
            for other, strength in sorted(agent.relationships.items(), key=lambda item: item[1], reverse=True)
        ) or "none"
        recent_events = "; ".join(event["description"] for event in self.world.events[-3:]) or "none"
        belief_bits = "; ".join(
            f"{belief.kind}={belief.text}"
            for belief in self.world.beliefs[-3:]
        ) or "none"
        return (
            f"Turn {self.turn}; weather={self.world.weather}; location={location_text}; "
            f"resources={resource_bits}; recent_events={recent_events}; relationships={relationship_bits}; "
            f"active beliefs={belief_bits}"
        )

    def _run_reflection(self, agent: Agent) -> str | None:
        summarized = agent.memory.reflect_and_summarize(current_time=self.turn)
        exaggerated_memory = self.router.reflect_and_hallucinate(summarized, entropy_factor=0.3)

        if not exaggerated_memory or "[FALLBACK]" in exaggerated_memory:
            print(f"[WARN] Reflection fallback for {agent.identity.name} at turn {self.turn}. Skipping.")
            return None

        # Save embedding vector to ChromaDB memory in real mode; demo memory ignores this as short-term lore.
        self.router.extract_vector(exaggerated_memory)
        beliefs = derive_beliefs_from_reflection(agent.identity.agent_id, exaggerated_memory, self.turn, self.random)
        self.world.add_beliefs(beliefs)
        agent.memory.add_memory(
            f"[LEGEND] {exaggerated_memory}",
            importance=0.9,
            timestamp=self.turn,
        )
        return exaggerated_memory

    def _dump_sandbox_state(self):
        state_data = []
        for agent in self.agents:
            state_data.append({
                "id": agent.identity.agent_id,
                "name": agent.identity.name,
                "x": agent.state.x,
                "y": agent.state.y,
                "emotion": agent.state.emotion,
                "action": agent.state.current_action,
                "speech": agent.state.speech,
                "location_id": self.agent_locations.get(agent.identity.agent_id),
                "relationships": {
                    other_id: strength
                    for other_id, strength in sorted(agent.relationships.items())
                },
            })

        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)
        try:
            with open(os.path.join(static_dir, "sandbox_state.json"), "w", encoding="utf-8") as f:
                json.dump(
                    {"turn": self.turn, "agents": state_data, "world": self.world.to_dict()},
                    f,
                    ensure_ascii=False,
                )
        except Exception as e:
            print(f"[WARN] Failed to write sandbox state: {e}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Entropy Civil simulation.")
    parser.add_argument("--demo", action="store_true", help="Run without Ollama/PostgreSQL/ChromaDB using deterministic demo data.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for deterministic demo/sandbox movement.")
    parser.add_argument("--turns", type=int, default=None, help="Run a fixed number of turns, then exit.")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds to wait between turns.")
    parser.add_argument("--agents", type=int, default=5, help="Number of agents to simulate.")
    return parser.parse_args()


def main():
    args = parse_args()
    sim = Simulation(num_agents=args.agents, demo_mode=args.demo, seed=args.seed)
    mode = "demo" if args.demo else "continuous"
    if args.turns is None:
        print(f"Starting {mode} simulation... Press Ctrl+C to stop.")
    else:
        print(f"Starting {mode} simulation for {args.turns} turns...")

    try:
        turns_run = 0
        while args.turns is None or turns_run < args.turns:
            sim.step()
            turns_run += 1
            if args.turns is None or turns_run < args.turns:
                time.sleep(args.sleep)
    except KeyboardInterrupt:
        print("Simulation paused.")


if __name__ == "__main__":
    main()
