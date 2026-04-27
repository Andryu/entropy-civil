import json
import random
import subprocess
import sys
import unittest
from pathlib import Path

from backend.agent import Agent
from backend.world_state import WorldState, derive_beliefs_from_reflection


class MythFeedbackLoopTest(unittest.TestCase):
    def test_derive_beliefs_from_reflection_creates_taboo_from_myth(self):
        beliefs = derive_beliefs_from_reflection(
            agent_id="demo-agent-0",
            reflection="The river spirit punished those who fished at dawn, so the village learned to avoid the river before sunrise.",
            turn=7,
            rng=random.Random(3),
        )

        self.assertGreaterEqual(len(beliefs), 1)
        kinds = {belief.kind for belief in beliefs}
        self.assertIn("taboo", kinds)
        self.assertTrue(any("avoid" in belief.text.lower() for belief in beliefs), beliefs)

    def test_agent_decision_context_respects_active_belief_taboo(self):
        agent = Agent("Agent-0", "Practical and cautious")
        agent.state.needs.survival = 0.2
        agent.state.energy = 0.8

        action = agent.decide_next_action(
            "Turn 7; weather=misty; active beliefs: taboo=avoid fishing at dawn near the river; "
            "prophecy=the meadow will feed the village."
        )

        lowered = action.lower()
        self.assertTrue(
            any(keyword in lowered for keyword in ["meadow", "forest", "gather", "forage", "berries"]),
            msg=action,
        )
        self.assertFalse("fish" in lowered and "river" in lowered, msg=action)

    def test_world_state_serializes_active_beliefs(self):
        world = WorldState.create_default(random.Random(9))
        beliefs = derive_beliefs_from_reflection(
            agent_id="demo-agent-1",
            reflection="The hidden name of the cave became a sacred law, and the stars promised a return in spring.",
            turn=11,
            rng=random.Random(11),
        )
        world.add_beliefs(beliefs)

        data = world.to_dict()
        self.assertIn("beliefs", data)
        self.assertGreaterEqual(len(data["beliefs"]), 1)
        self.assertTrue(any(belief["kind"] in {"law", "prophecy", "sacred_location", "omen"} for belief in data["beliefs"]))

    def test_simulation_context_includes_active_beliefs(self):
        repo = Path(__file__).resolve().parents[1]
        state_file = repo / "backend" / "static" / "sandbox_state.json"
        if state_file.exists():
            state_file.unlink()

        result = subprocess.run(
            [
                sys.executable,
                str(repo / "backend" / "simulation.py"),
                "--demo",
                "--seed",
                "5",
                "--turns",
                "6",
                "--sleep",
                "0",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            timeout=20,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        state = json.loads(state_file.read_text())
        self.assertIn("beliefs", state["world"])
        self.assertGreaterEqual(len(state["world"]["beliefs"]), 1)
        self.assertTrue(any(belief["kind"] in {"taboo", "omen", "law", "prophecy", "ritual", "sacred_location"} for belief in state["world"]["beliefs"]))


if __name__ == "__main__":
    unittest.main()
