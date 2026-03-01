from agent import Agent
from memory import MemorySystem
from llm_router import LLMRouter
from database import SessionLocal, engine, Base
from epoch_detector import detect_and_record_epoch
from chronicle_summarizer import generate_chronicle
import models
import json
import os
import random
from sandbox_utils import parse_agent_action

# Ensure tables are created
Base.metadata.create_all(bind=engine)

class Simulation:
    def __init__(self, num_agents: int = 5):
        self.router = LLMRouter()
        self.agents = [Agent(f"Agent-{i}", "Curious pioneer") for i in range(num_agents)]

        # Inject memory system into agents
        for a in self.agents:
            a.memory = MemorySystem(agent_id=a.identity.agent_id)

        # Fix #2: Resume from the last turn stored in the DB
        self.turn = self._resume_turn()
        print(f"[Simulation] Resuming from turn {self.turn}.")

    def _resume_turn(self) -> int:
        """Read the last persisted turn from the DB to enable seamless restart."""
        db = SessionLocal()
        try:
            last_event = db.query(models.SimulationEvent).order_by(
                models.SimulationEvent.turn.desc()
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

        db = SessionLocal()
        try:
            # 1. Daily Actions (Local LLM Routing)
            for agent in self.agents:
                action = self.router.chat_daily(f"What will {agent.identity.name} do?")

                if not action or "[FALLBACK]" in action:
                    print(f"[WARN] Agent {agent.identity.name} got a fallback response at turn {self.turn}. Skipping save.")
                    continue

                agent.memory.add_memory(action, importance=0.5, timestamp=self.turn)

                # --- Sandbox State Update ---
                parsed = parse_agent_action(action)
                agent.state.emotion = parsed["emotion"]
                agent.state.current_action = parsed["action"]
                agent.state.speech = parsed["speech"]
                # Move slightly
                agent.state.x = max(0.0, min(100.0, agent.state.x + random.uniform(-10.0, 10.0)))
                agent.state.y = max(0.0, min(100.0, agent.state.y + random.uniform(-10.0, 10.0)))

                # Save Daily Action to DB
                event = models.SimulationEvent(
                    turn=self.turn,
                    agent_id=agent.identity.agent_id,
                    event_type="DAILY_ACTION",
                    content=action
                )
                db.add(event)

            # 2. Nightly Reflection & Entropy Injection (Cloud LLM Routing)
            # Occurs every 5 turns
            if self.turn % 5 == 0 and self.turn > 0:
                print(">>> The agents are reflecting... (Entropy Injection)")
                for agent in self.agents:
                    summarized = agent.memory.reflect_and_summarize(current_time=self.turn)
                    exaggerated_memory = self.router.reflect_and_hallucinate(summarized, entropy_factor=0.3)

                    if not exaggerated_memory or "[FALLBACK]" in exaggerated_memory:
                        print(f"[WARN] Reflection fallback for {agent.identity.name} at turn {self.turn}. Skipping.")
                        continue

                    # Save Reflection to DB
                    event = models.SimulationEvent(
                        turn=self.turn,
                        agent_id=agent.identity.agent_id,
                        event_type="REFLECTION",
                        content=exaggerated_memory
                    )
                    db.add(event)

                    # Save embedding vector to ChromaDB memory
                    vec = self.router.extract_vector(exaggerated_memory)
                    agent.memory.add_memory(
                        f"[LEGEND] {exaggerated_memory}",
                        importance=0.9,
                        timestamp=self.turn
                    )

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Turn {self.turn} failed: {e}")
        finally:
            db.close()

        # Phase 5: Auto-detect and record new epochs every N turns
        detect_and_record_epoch(self.turn)

        # Phase 5: Generate chronicle summary every 100 turns
        generate_chronicle(self.turn)

        # Output current state for Sandbox View
        self._dump_sandbox_state()

        self.turn += 1

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
                "speech": agent.state.speech
            })
        
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)
        try:
            with open(os.path.join(static_dir, "sandbox_state.json"), "w", encoding="utf-8") as f:
                json.dump({"turn": self.turn, "agents": state_data}, f, ensure_ascii=False)
        except Exception as e:
            print(f"[WARN] Failed to write sandbox state: {e}")

if __name__ == "__main__":
    import time
    sim = Simulation(num_agents=5)
    print("Starting continuous simulation... Press Ctrl+C to stop.")
    try:
        while True:
            sim.step()
            time.sleep(2)  # Wait 2 seconds between turns for readability
    except KeyboardInterrupt:
        print("Simulation paused.")
