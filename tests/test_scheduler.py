import unittest
from datetime import date

from life_os.db import EntityInput, LifeOSRepository
from life_os.scheduler import CapacityProfile, SchedulingEngine


class SchedulerTests(unittest.TestCase):
    def test_scheduler_respects_dependencies(self):
        repo = LifeOSRepository("sqlite:///:memory:")

        blocked = repo.add_entity(EntityInput(entity_type="task", title="blocked", urgency=5, importance=5, expected_gain=5))
        prerequisite = repo.add_entity(EntityInput(entity_type="task", title="prerequisite", urgency=1, importance=1, expected_gain=1))
        repo.add_dependency(blocked, prerequisite)

        runnable = repo.add_entity(EntityInput(entity_type="task", title="runnable", urgency=4, importance=4, expected_gain=4))

        engine = SchedulingEngine(repo)
        blocks = engine.schedule_day(CapacityProfile(day=date(2026, 4, 7), total_hours=2, deep_work_hours=1))

        task_ids = [b["task_id"] for b in blocks]
        self.assertIn(runnable, task_ids)
        self.assertNotIn(blocked, task_ids)
        repo.close()


if __name__ == "__main__":
    unittest.main()
