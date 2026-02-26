from typing import Dict, Any, List
from src.llm.base import LLMProvider
from src.agents.reviewer import ReviewerAgent
from src.agents.impact_analyst import ImpactAnalystAgent
from src.mcp.client import MCPClientManager
from src.gitlab.connector import GitLabConnector
from src.db.connector import MongoDBConnector
from src.rag.indexer import ASTDerivedIndexer
from src.rag.retriever import HybridRetriever
from src.sonarqube.connector import SonarQubeConnector
from src.dynatrace.connector import DynatraceConnector

class Orchestrator:
    """
    Main entry point for the Agentic SDLC Co-pilot.
    Routes requests to specialized agents.
    """
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.mcp_manager = MCPClientManager()

        # Connectors
        self.gitlab = GitLabConnector(self.mcp_manager)
        self.mongo = MongoDBConnector(self.mcp_manager)
        self.sonar = SonarQubeConnector()
        self.dynatrace = DynatraceConnector()

        # RAG Engine
        self.indexer = ASTDerivedIndexer(self.mongo)
        self.retriever = HybridRetriever(self.mongo)

        # Sub-Agents
        self.reviewer = ReviewerAgent(llm, self.gitlab, self.retriever, self.sonar)
        self.impact_analyst = ImpactAnalystAgent(llm, self.gitlab, self.retriever, self.dynatrace)

    async def initialize(self):
        print("[Orchestrator] Initializing system...")
        await self.gitlab.initialize()
        await self.mongo.initialize()
        # Sonar/Dynatrace might need init in future
        print("[Orchestrator] System Ready.")

    async def run_chat(self, query: str) -> str:
        """
        Talk-to-code flow.
        """
        print(f"[Orchestrator] Chat Query: {query}")

        # 1. Retrieve Context
        # Heuristic: assume query mentions a service or concept
        chunks = await self.retriever.search("Unknown", query, limit=3)

        context = "Context from Knowledge Base:\n"
        for chunk in chunks:
            context += f"- {chunk.get('content', '')[:200]}...\n"

        # 2. LLM Answer
        system_prompt = "You are an expert software architect assisting a developer."
        return await self.llm.generate_response(system_prompt, f"Context:\n{context}\n\nQuestion: {query}")

    async def run_review(self, project_id: str, mr_iid: int):
        """
        Routes to Reviewer Agent.
        """
        return await self.reviewer.review_mr(project_id, mr_iid)

    async def run_impact(self, project_id: str, service_name: str):
        """
        Routes to Impact Analyst Agent.
        """
        return await self.impact_analyst.analyze_impact(project_id, service_name)

    async def ingest_changes(self, project_id: str, service_name: str, files: Dict[str, str]):
        """
        Routes to Indexer.
        """
        await self.indexer.ingest_changes(project_id, service_name, files)
