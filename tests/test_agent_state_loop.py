import unittest

from backend.agent import Agent


class CapturingBrain:
    def __init__(self, response: str = "Agent-0 gathers food by the river."):
        self.response = response
        self.prompts = []

    def chat_daily(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class AgentStateLoopTest(unittest.TestCase):
    def test_decide_next_action_prefers_food_when_survival_is_low(self):
        agent = Agent("Agent-0", "Practical and cautious")
        agent.state.needs.survival = 0.2
        agent.state.boredom = 0.1
        agent.state.energy = 0.8

        action = agent.decide_next_action("Winter is coming and the pantry is nearly empty.")

        self.assertIsInstance(action, str)
        self.assertTrue(
            any(keyword in action.lower() for keyword in ["food", "gather", "hunt", "fish", "eat"]),
            msg=action,
        )

    def test_decide_next_action_prefers_exploration_when_boredom_is_high(self):
        agent = Agent("Agent-1", "Restless and curious")
        agent.state.needs.survival = 0.9
        agent.state.boredom = 0.95
        agent.state.curiosity = 0.9
        agent.state.energy = 0.7

        action = agent.decide_next_action("The settlement feels safe but uneventful.")

        self.assertIsInstance(action, str)
        self.assertTrue(
            any(keyword in action.lower() for keyword in ["explore", "discover", "wander", "search", "forest"]),
            msg=action,
        )

    def test_decide_next_action_includes_state_and_relationship_context_in_prompt(self):
        agent = Agent("Agent-2", "Thoughtful and social")
        brain = CapturingBrain()
        agent.brain = brain
        agent.state.needs.survival = 0.65
        agent.state.needs.belonging = 0.3
        agent.state.boredom = 0.4
        agent.state.curiosity = 0.8
        agent.relationships = {"ally-1": 0.85, "rival-9": -0.4}

        result = agent.decide_next_action("A council is meeting near the fire pit.")

        self.assertEqual(result, brain.response)
        self.assertEqual(len(brain.prompts), 1)
        prompt = brain.prompts[0]
        self.assertIn("Agent-2", prompt)
        self.assertIn("survival", prompt)
        self.assertIn("boredom", prompt)
        self.assertIn("curiosity", prompt)
        self.assertIn("ally-1", prompt)
        self.assertIn("rival-9", prompt)
        self.assertIn("relationship", prompt.lower())

    def test_update_state_after_action_reduces_energy_and_increases_belonging_for_social_actions(self):
        agent = Agent("Agent-3", "Helpful and warm")
        agent.state.energy = 0.8
        agent.state.boredom = 0.6
        agent.state.needs.belonging = 0.4
        agent.relationships = {"Agent-4": 0.0}

        agent.update_state_after_action("Agent-3 shares food with Agent-4 by the fire.")

        self.assertLess(agent.state.energy, 0.8)
        self.assertLess(agent.state.boredom, 0.6)
        self.assertGreater(agent.state.needs.belonging, 0.4)
        self.assertGreater(agent.relationships["Agent-4"], 0.0)

    def test_update_state_after_action_raises_survival_for_food_gathering_and_caps_values(self):
        agent = Agent("Agent-5", "Steady and practical")
        agent.state.energy = 0.98
        agent.state.boredom = 0.05
        agent.state.needs.survival = 0.95

        agent.update_state_after_action("Agent-5 gathers berries and eats a full meal after fishing.")

        self.assertGreater(agent.state.needs.survival, 0.95)
        self.assertLessEqual(agent.state.energy, 1.0)
        self.assertGreaterEqual(agent.state.boredom, 0.0)


if __name__ == "__main__":
    unittest.main()
