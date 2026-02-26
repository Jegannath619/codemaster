import asyncio
import unittest
import json
from unittest.mock import MagicMock
from src.agent import CodeMasterAgent
from src.llm.openai_client import OpenAIProvider
from src.rag.indexer import ASTDerivedIndexer
from src.rag.retriever import HybridRetriever
from src.analysis.dependency_graph import DeterministicGraphBuilder

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

    def test_dkb_indexer_parsing(self):
        indexer = ASTDerivedIndexer(MagicMock())

        # Test C# parsing for Classes and Methods
        csharp_code = """
        public class OrderService : IOrderService {
            private readonly IRepo _repo;

            public void CreateOrder() {
                _repo.Save();
            }
        }
        """
        nodes = indexer._parse_file("OrderService.cs", csharp_code)

        # Expecting: 1 Class Node + 1 Method Node
        class_node = next((n for n in nodes if n["type"] == "class"), None)
        method_node = next((n for n in nodes if n["type"] == "method"), None)

        self.assertIsNotNone(class_node)
        self.assertEqual(class_node["name"], "OrderService")
        self.assertEqual(class_node["implements"], "IOrderService")

        self.assertIsNotNone(method_node)
        self.assertEqual(method_node["name"], "CreateOrder")

    def test_dkb_graph_builder(self):
        # Test controller injection logic
        builder = DeterministicGraphBuilder(MagicMock())

        # Mock file content fetch
        async def mock_get_content(*args):
            return "public class OrderController { private readonly IOrderService _service; }"

        builder.gitlab.get_file_content = MagicMock(side_effect=mock_get_content)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        deps = loop.run_until_complete(builder._analyze_controller_injections("123", "src/Order/OrderController.cs"))
        self.assertIn("IOrderService", deps)
        loop.close()

    def test_retriever_ranking(self):
        mock_mongo = MagicMock()
        future = asyncio.Future()
        future.set_result([])
        mock_mongo.mcp_manager.call_tool.return_value = future

        retriever = HybridRetriever(mock_mongo)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        results = loop.run_until_complete(retriever.search("ServiceA", "payment"))
        self.assertTrue(len(results) > 0)

        loop.close()

if __name__ == '__main__':
    unittest.main()
