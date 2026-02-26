import asyncio
import unittest
from unittest.mock import MagicMock
from src.agent import CodeMasterAgent
from src.llm.openai_client import OpenAIProvider

class TestCodeMasterAgent(unittest.TestCase):
    def setUp(self):
        self.llm = OpenAIProvider()
        self.agent = CodeMasterAgent(self.llm)

    def test_initialization(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.agent.initialize())
        loop.close()
        # If no exception, it passed
        self.assertTrue(True)

    def test_code_review_workflow(self):
        # We can't easily mock async calls in standard unittest without aiounittest or pytest-asyncio
        # but for this environment, we will just run the agent methods and check if they return strings
        # as the underlying connectors are already mocked.

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize
        loop.run_until_complete(self.agent.initialize())

        # Run Code Review
        result = loop.run_until_complete(self.agent.run_code_review("123", 1))
        self.assertIsInstance(result, str)
        self.assertIn("solid", result)

        # Run Impact Analysis
        impact = loop.run_until_complete(self.agent.run_impact_analysis("123", "ServiceA"))
        self.assertIsInstance(impact, str)
        self.assertIn("ServiceB", impact)

        loop.close()

if __name__ == '__main__':
    unittest.main()
