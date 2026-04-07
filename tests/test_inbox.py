import unittest

from sqlalchemy import select

from life_os.db import DBInboxClassification, LifeOSRepository
from life_os.inbox import BrainDumpProcessor


class InboxTests(unittest.TestCase):
    def test_brain_dump_classifies_and_persists_segments(self):
        repo = LifeOSRepository("sqlite:///:memory:")
        processor = BrainDumpProcessor(repo)

        result = processor.process("learn Unreal, fix finances, buy keyboard")

        self.assertEqual(result["segments"], 3)
        self.assertGreaterEqual(result["entities_created_or_linked"], 3)

        with repo.session_scope() as db:
            rows = db.execute(select(DBInboxClassification)).scalars().all()
            self.assertEqual(len(rows), 3)
        repo.close()


if __name__ == "__main__":
    unittest.main()
