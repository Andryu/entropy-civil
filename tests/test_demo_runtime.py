import unittest

from backend.demo_runtime import DemoLLMRouter, DemoMemorySystem


class DemoRuntimeTest(unittest.TestCase):
    def test_demo_router_is_deterministic_for_same_seed(self):
        first = DemoLLMRouter(seed=42)
        second = DemoLLMRouter(seed=42)

        first_actions = [first.chat_daily("What will Agent-0 do?") for _ in range(4)]
        second_actions = [second.chat_daily("What will Agent-0 do?") for _ in range(4)]

        self.assertEqual(first_actions, second_actions)
        self.assertTrue(all("[DEMO]" in action for action in first_actions))

    def test_demo_memory_reflects_and_clears_short_term_memories(self):
        memory = DemoMemorySystem(agent_id="agent-1")
        memory.add_memory("Agent gathered berries.", importance=0.5, timestamp=3)

        reflected = memory.reflect_and_summarize(current_time=5)

        self.assertEqual(len(reflected), 1)
        self.assertEqual(reflected[0].content, "Agent gathered berries.")
        self.assertEqual(memory.short_term, [])


if __name__ == "__main__":
    unittest.main()
