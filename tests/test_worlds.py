import unittest

from garden_ecosystem.worlds import LifeState, MemoryWorld, MigrationError, PortableAgent, migrate, self_test


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.source = MemoryWorld("source")
        self.target = MemoryWorld("target")
        self.agent = PortableAgent("agent-1", {"role": "reviewer"}, capabilities=("read",))

    def test_successful_migration_preserves_identity_and_single_copy(self):
        self.source.add(self.agent)
        result = migrate(self.source, self.target, self.agent.agent_id)
        self.assertEqual(result.status, "completed")
        self.assertNotIn(self.agent.agent_id, self.source.agents)
        self.assertEqual(self.target.agents[self.agent.agent_id].agent_id, self.agent.agent_id)
        self.assertEqual(self.target.agents[self.agent.agent_id].capabilities, ("read",))

    def test_rejection_rolls_back_source(self):
        target = MemoryWorld("target", reject={self.agent.agent_id})
        self.source.add(self.agent)
        result = migrate(self.source, target, self.agent.agent_id)
        self.assertEqual(result.status, "rolled_back")
        self.assertIn(self.agent.agent_id, self.source.agents)
        self.assertNotIn(self.agent.agent_id, target.agents)

    def test_commit_failure_removes_target_copy(self):
        target = MemoryWorld("target", fail_commit={self.agent.agent_id})
        self.source.add(self.agent)
        result = migrate(self.source, target, self.agent.agent_id)
        self.assertEqual(result.status, "rolled_back")
        self.assertNotIn(self.agent.agent_id, target.agents)
        self.assertNotIn(self.agent.agent_id, target.staging)

    def test_double_failure_requires_manual_recovery(self):
        source = MemoryWorld("source", fail_restore={self.agent.agent_id})
        target = MemoryWorld("target", fail_commit={self.agent.agent_id})
        source.add(self.agent)
        result = migrate(source, target, self.agent.agent_id)
        self.assertEqual(result.status, "recovery_required")
        self.assertTrue(result.needs_manual_recovery)
        self.assertIsNotNone(result.rollback_error)

    def test_missing_source_does_not_change_target(self):
        result = migrate(self.source, self.target, "missing")
        self.assertEqual(result.status, "failed")
        self.assertEqual(self.target.agents, {})

    def test_existing_target_is_not_overwritten(self):
        self.source.add(self.agent)
        self.target.add(self.agent)
        result = migrate(self.source, self.target, self.agent.agent_id)
        self.assertEqual(result.status, "rolled_back")
        self.assertIn(self.agent.agent_id, self.source.agents)

    def test_self_test_does_not_pollute_real_world(self):
        self.assertTrue(self_test(self.target, self.agent))
        self.assertEqual(self.target.agents, {})
        self.assertEqual(self.target.staging, {})

    def test_snapshot_is_isolated_from_nested_mutations(self):
        self.source.add(self.agent)
        snapshot = self.source.snapshot(self.agent.agent_id)
        snapshot.attributes["role"] = "changed"
        self.assertEqual(self.source.agents[self.agent.agent_id].attributes["role"], "reviewer")

    def test_lifecycle_defaults_to_alive(self):
        self.assertEqual(self.agent.lifecycle, LifeState.ALIVE)
        with self.assertRaises(MigrationError):
            self.source.add(PortableAgent("bad", {}, lifecycle="traveling"))


if __name__ == "__main__":
    unittest.main()
