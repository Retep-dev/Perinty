"""Opt-in live test. Uses unique fixtures, never clears existing user data."""
import os
import unittest


@unittest.skipUnless(os.getenv("RUN_LIVE_RAG_TEST") == "1", "Set RUN_LIVE_RAG_TEST=1 and PERINTY_TEST_URL to test live services")
class LiveRAGTest(unittest.TestCase):
    def test_complete_flow(self):
        from scripts.smoke_test import run
        run(os.environ["PERINTY_TEST_URL"])


if __name__ == "__main__":
    unittest.main()
