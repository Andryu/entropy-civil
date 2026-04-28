import unittest

from backend.event_schema import build_structured_event_data, simulation_event_to_dict


class StructuredEventsTest(unittest.TestCase):
    def test_build_structured_event_data_for_daily_action_contains_core_fields(self):
        structured = build_structured_event_data(
            event_type="DAILY_ACTION",
            agent_id="demo-agent-0",
            content="Agent-0 gathers food near the river with Agent-1.",
            turn=12,
            location_id="river",
            world_event={
                "location_id": "river",
                "resource_id": "food",
                "effect": "increase",
                "amount": 2,
            },
        )

        self.assertEqual(structured["actor"], "demo-agent-0")
        self.assertEqual(structured["action"], "gather")
        self.assertEqual(structured["location"], "river")
        self.assertEqual(structured["effect"], "increase")
        self.assertIn("resource:food", structured["tags"])
        self.assertIn("daily_action", structured["tags"])
        self.assertIn("resource:food", structured["tags"])
        self.assertIsNone(structured["causal_parent_id"])

    def test_build_structured_event_data_for_reflection_links_to_parent_event(self):
        structured = build_structured_event_data(
            event_type="REFLECTION",
            agent_id="demo-agent-0",
            content="The river spirit punished those who fished at dawn.",
            turn=13,
            causal_parent_id=101,
            entropy_level=0.8,
        )

        self.assertEqual(structured["actor"], "demo-agent-0")
        self.assertEqual(structured["action"], "reflect")
        self.assertEqual(structured["causal_parent_id"], 101)
        self.assertGreaterEqual(structured["entropy_level"], 0.8)
        self.assertIn("reflection", structured["tags"])
        self.assertIn("myth", structured["tags"])

    def test_simulation_event_to_dict_exposes_structured_fields(self):
        row = {
            "id": 7,
            "turn": 14,
            "agent_id": "demo-agent-1",
            "event_type": "DAILY_ACTION",
            "content": "Agent-1 shares food by the fire.",
            "structured_data": {
                "actor": "demo-agent-1",
                "action": "share",
                "location": "fire_pit",
                "target": "Agent-2",
                "cause": "social bond",
                "effect": "belonging +0.12",
                "tags": ["daily_action", "social"],
                "importance": 0.7,
                "entropy_level": 0.0,
                "causal_parent_id": None,
            },
        }

        payload = simulation_event_to_dict(row)

        self.assertEqual(payload["id"], 7)
        self.assertEqual(payload["actor"], "demo-agent-1")
        self.assertEqual(payload["action"], "share")
        self.assertEqual(payload["location"], "fire_pit")
        self.assertEqual(payload["target"], "Agent-2")
        self.assertEqual(payload["tags"], ["daily_action", "social"])
        self.assertIn("structured", payload)


if __name__ == "__main__":
    unittest.main()
