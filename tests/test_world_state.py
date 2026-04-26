import random
import unittest

from backend.world_state import WorldState, apply_agent_action_to_world


class WorldStateTest(unittest.TestCase):
    def test_default_world_contains_locations_and_resources(self):
        world = WorldState.create_default(random.Random(3))

        self.assertGreaterEqual(len(world.locations), 4)
        self.assertIn("river", world.locations)
        self.assertIn("forest", world.locations)
        self.assertIn("food", world.resources)
        self.assertIn("wood", world.resources)
        self.assertIn("stone", world.resources)

    def test_agent_action_updates_resource_and_location_deterministically(self):
        rng = random.Random(7)
        world = WorldState.create_default(rng)
        before_food = world.resources["food"]
        before_river_activity = world.locations["river"].activity

        event = apply_agent_action_to_world(
            world,
            "demo-agent-0",
            "Agent-0 [DEMO] gathers bright berries near the river and shares them by the fire.",
            rng,
        )

        self.assertEqual(event["agent_id"], "demo-agent-0")
        self.assertEqual(event["location_id"], "river")
        self.assertEqual(event["resource_id"], "food")
        self.assertEqual(event["effect"], "increase")
        self.assertGreater(world.resources["food"], before_food)
        self.assertEqual(world.locations["river"].activity, before_river_activity + 1)
        self.assertEqual(world.locations["river"].last_event, event["description"])

    def test_same_seed_and_actions_produce_same_world_state(self):
        action = "Agent-0 [DEMO] repairs a fishing net while humming an old rhythm."

        def run_once():
            rng = random.Random(11)
            world = WorldState.create_default(rng)
            apply_agent_action_to_world(world, "demo-agent-0", action, rng)
            return world.to_dict()

        self.assertEqual(run_once(), run_once())


if __name__ == "__main__":
    unittest.main()
