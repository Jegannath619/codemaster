import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from src.webhook_server import app

class TestWebhookServer(unittest.TestCase):
    def setUp(self):
        # Patch the orchestrator in the webhook server module
        self.orch_patcher = patch("src.webhook_server.orchestrator")
        self.mock_orch = self.orch_patcher.start()

        # Configure mock orchestrator behaviors
        self.mock_orch.gitlab.get_file_content = AsyncMock(return_value="public class Mock {}")
        self.mock_orch.ingest_changes = AsyncMock()
        self.mock_orch.run_review = AsyncMock()

        self.client = TestClient(app)

    def tearDown(self):
        self.orch_patcher.stop()

    def test_webhook_push_event(self):
        payload = {
            "object_kind": "push",
            "project_id": 123,
            "checkout_sha": "abc1234",
            "commits": [
                {
                    "added": ["src/ServiceA/NewFile.cs"],
                    "modified": ["src/ServiceA/OldFile.cs"],
                    "removed": []
                }
            ]
        }
        headers = {"X-Gitlab-Token": "dummy_secret"}

        response = self.client.post("/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "processing")

    def test_webhook_mr_event(self):
        payload = {
            "object_kind": "merge_request",
            "project": {"id": 123},
            "object_attributes": {
                "iid": 1,
                "action": "open"
            }
        }
        headers = {"X-Gitlab-Token": "dummy_secret"}

        response = self.client.post("/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Merge Request queued for review")

if __name__ == '__main__':
    unittest.main()
