import json
import subprocess
import sys
import unittest
from pathlib import Path


class DemoSimulationCliTest(unittest.TestCase):
    def test_demo_cli_runs_fixed_number_of_turns_without_service_dependencies(self):
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
                "7",
                "--turns",
                "2",
                "--sleep",
                "0",
            ],
            cwd=repo,
            text=True,
            capture_output=True,
            timeout=10,
        )

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Starting demo simulation", result.stdout)
        self.assertTrue(state_file.exists())
        state = json.loads(state_file.read_text())
        self.assertEqual(state["turn"], 1)
        self.assertEqual(len(state["agents"]), 5)
        self.assertIn("world", state)
        self.assertIn("resources", state["world"])
        self.assertIn("locations", state["world"])
        self.assertGreaterEqual(len(state["world"]["locations"]), 4)
        self.assertTrue(any(agent.get("location_id") for agent in state["agents"]))

    def test_demo_cli_reproduces_same_sandbox_state_for_same_seed(self):
        repo = Path(__file__).resolve().parents[1]
        state_file = repo / "backend" / "static" / "sandbox_state.json"

        states = []
        for _ in range(2):
            result = subprocess.run(
                [
                    sys.executable,
                    str(repo / "backend" / "simulation.py"),
                    "--demo",
                    "--seed",
                    "11",
                    "--turns",
                    "3",
                    "--sleep",
                    "0",
                ],
                cwd=repo,
                text=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            states.append(json.loads(state_file.read_text()))

        self.assertEqual(states[0], states[1])


if __name__ == "__main__":
    unittest.main()
