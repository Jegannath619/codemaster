import asyncio
import unittest
import json
from unittest.mock import MagicMock
from src.agent import CodeMasterAgent
from src.llm.openai_client import OpenAIProvider
from src.rag.indexer import CodeIndexer
from src.rag.retriever import HybridRetriever

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

    def test_indexer_parsing(self):
        indexer = CodeIndexer(MagicMock())

        # Test C# parsing
        csharp_code = """
        public void MethodA() {
            var x = 1;
        }

        private string MethodB(int y) {
            return "test";
        }
        """
        chunks = indexer._chunk_file("Test.cs", csharp_code)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["name"], "MethodA")
        self.assertEqual(chunks[1]["name"], "MethodB")

    def test_retriever_ranking(self):
        # We need to mock the async call chain: mongo.mcp_manager.call_tool
        mock_mongo = MagicMock()

        # Setup async mock for call_tool
        future = asyncio.Future()
        future.set_result([]) # Return empty list so it falls back to internal mock data
        mock_mongo.mcp_manager.call_tool.return_value = future

        retriever = HybridRetriever(mock_mongo)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # We expect the mock in HybridRetriever to return something
        results = loop.run_until_complete(retriever.search("ServiceA", "payment"))
        self.assertTrue(len(results) > 0)
        self.assertIn("score", results[0])

        loop.close()

if __name__ == '__main__':
    unittest.main()
