import asyncio
from typing import Optional, Dict, Any
from src.llm.base import LLMProvider
from src.mcp.client import MCPClientManager
from src.gitlab.connector import GitLabConnector
from src.db.connector import MongoDBConnector
from src.analysis.dependency_graph import DependencyGraphBuilder
from src.analysis.knowledge_base import KnowledgeBase
from src.analysis.context_builder import ContextBuilder

class CodeMasterAgent:
    """
    The main agent orchestrating code analysis, review, and suggestions.
    """
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.mcp_manager = MCPClientManager()
        self.gitlab = GitLabConnector(self.mcp_manager)
        self.mongo = MongoDBConnector(self.mcp_manager)

        # Initialize Analysis Engine
        self.knowledge_base = KnowledgeBase(self.mongo)
        self.graph_builder = DependencyGraphBuilder(self.gitlab)
        self.context_builder = ContextBuilder(self.gitlab, self.graph_builder, self.knowledge_base)

    async def initialize(self):
        """
        Initializes connections to external services.
        """
        print("[Agent] Initializing...")
        await self.gitlab.initialize()
        await self.mongo.initialize()
        print("[Agent] Ready.")

    async def run_code_review(self, project_id: str, mr_iid: int):
        """
        Performs a code review for a specific Merge Request.
        """
        print(f"[Agent] Starting Code Review for Project {project_id}, MR {mr_iid}...")

        # 1. Build Context (includes Graph + KB chunks)
        context = await self.context_builder.build_context(project_id, mr_iid)

        # 2. Ask LLM
        system_prompt = "You are a senior software architect specializing in microservices."
        user_prompt = f"{context}\n\nPlease review the changes above. Focus on:\n1. Logic Errors\n2. Security Flaws (especially cross-service)\n3. Performance Impact"

        review_comments = await self.llm.generate_response(system_prompt, user_prompt)

        # 3. Save Result
        await self.mongo.save_analysis(project_id, mr_iid, {"review": review_comments})

        print("[Agent] Review Completed.")
        return review_comments

    async def run_impact_analysis(self, project_id: str, service_name: str):
        """
        Analyzes the impact of changing a specific service.
        """
        print(f"[Agent] Analyzing impact for service: {service_name}...")
        # Mock logic for impact analysis
        # In reality, this would query the dependency graph to find all consumers.

        return f"Impact Analysis: Changing {service_name} will require updates in ServiceB and ServiceC due to shared API contracts."

    async def suggest_changes(self, project_id: str, requirement: str):
        """
        Suggests code changes based on a high-level requirement.
        """
        print(f"[Agent] Generating code suggestions for: {requirement}")

        system_prompt = "You are an expert coder. Generate code snippets based on the requirement."
        suggestion = await self.llm.generate_response(system_prompt, requirement)

        return suggestion
