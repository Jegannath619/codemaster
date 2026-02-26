import asyncio
import unittest
import json
from unittest.mock import MagicMock
from src.agent import CodeMasterAgent
from src.llm.openai_client import OpenAIProvider
from src.analysis.dependency_graph import DependencyGraphBuilder

class TestCodeMasterAgent(unittest.TestCase):
    def setUp(self):
        self.llm = OpenAIProvider()
        self.agent = CodeMasterAgent(self.llm)

    def test_initialization(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.agent.initialize())
        loop.close()
        self.assertTrue(True)

    def test_code_review_workflow(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.agent.initialize())
        result = loop.run_until_complete(self.agent.run_code_review("123", 1))

        self.assertIsInstance(result, str)
        self.assertIn("solid", result)
        loop.close()

    def test_appsettings_parsing(self):
        # Unit test for the parser logic
        parser = DependencyGraphBuilder(MagicMock())
        appsettings_content = json.dumps({
            "ServiceSettings": {
                "OrderServiceUrl": "http://order-service:5000",
                "PaymentServiceUrl": "https://payment-api.internal"
            },
            "ConnectionStrings": {
                "MainDb": "mongodb://mongo:27017/db"
            }
        })
        deps = parser._parse_appsettings_dependencies(appsettings_content)
        self.assertIn("order-service", deps)
        self.assertIn("payment-api.internal", deps)
        self.assertIn("MongoDB", deps)

if __name__ == '__main__':
    unittest.main()
