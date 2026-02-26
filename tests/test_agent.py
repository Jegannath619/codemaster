import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from src.agents.orchestrator import Orchestrator
from src.llm.openai_client import OpenAIProvider

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.llm = OpenAIProvider()
        self.orchestrator = Orchestrator(self.llm)

        # Mock sub-agents and connectors to avoid real calls
        self.orchestrator.gitlab = MagicMock()
        self.orchestrator.gitlab.initialize = AsyncMock()
        self.orchestrator.gitlab.get_file_content = AsyncMock(return_value="mock content")
        self.orchestrator.gitlab.get_merge_request_diffs = AsyncMock(return_value=[])

        self.orchestrator.mongo = MagicMock()
        self.orchestrator.mongo.initialize = AsyncMock()

        self.orchestrator.indexer = MagicMock()
        self.orchestrator.indexer.ingest_changes = AsyncMock()

        self.orchestrator.retriever = MagicMock()
        self.orchestrator.retriever.search = AsyncMock(return_value=[{"content": "mock chunk"}])

        self.orchestrator.sonar = MagicMock()
        self.orchestrator.sonar.get_issues_for_project = AsyncMock(return_value=[])

        self.orchestrator.dynatrace = MagicMock()
        self.orchestrator.dynatrace.get_service_dependencies = AsyncMock(return_value={})
        self.orchestrator.dynatrace.get_service_metrics = AsyncMock(return_value={})

    def test_initialization(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.orchestrator.initialize())
        loop.close()
        self.assertTrue(self.orchestrator.gitlab.initialize.called)

    def test_chat_workflow(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        response = loop.run_until_complete(self.orchestrator.run_chat("How does auth work?"))
        self.assertIsInstance(response, str)
        self.assertTrue(self.orchestrator.retriever.search.called)
        loop.close()

    def test_review_routing(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Patch the reviewer agent specifically inside the orchestrator
        self.orchestrator.reviewer.review_mr = AsyncMock(return_value="Review Result")

        result = loop.run_until_complete(self.orchestrator.run_review("123", 1))
        self.assertEqual(result, "Review Result")
        loop.close()

    def test_impact_routing(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        self.orchestrator.impact_analyst.analyze_impact = AsyncMock(return_value="Impact Report")

        result = loop.run_until_complete(self.orchestrator.run_impact("123", "ServiceA"))
        self.assertEqual(result, "Impact Report")
        loop.close()

if __name__ == '__main__':
    unittest.main()
