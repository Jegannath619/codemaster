from typing import Dict, Any
from src.llm.base import LLMProvider
from src.gitlab.connector import GitLabConnector
from src.rag.retriever import HybridRetriever
from src.sonarqube.connector import SonarQubeConnector

class ReviewerAgent:
    """
    Agent responsible for Code Review.
    Orchestrates Context Mapper -> Intent Inference -> Risk Hypothesis.
    """
    def __init__(self, llm: LLMProvider, gitlab: GitLabConnector, retriever: HybridRetriever, sonar: SonarQubeConnector):
        self.llm = llm
        self.gitlab = gitlab
        self.retriever = retriever
        self.sonar = sonar

    async def review_mr(self, project_id: str, mr_iid: int) -> str:
        print(f"[Reviewer] Starting review for MR {mr_iid}...")

        # 1. Context Mapper: Get Diffs & Sonar Issues
        diffs = await self.gitlab.get_merge_request_diffs(project_id, mr_iid)
        sonar_issues = await self.sonar.get_issues_for_project(project_id) # Mocked call

        # 2. Build Prompt Context
        context = "### Diffs ###\n"
        for diff in diffs:
            context += f"File: {diff['new_path']}\n{diff['diff']}\n"

        context += "\n### Static Analysis (SonarQube) ###\n"
        for issue in sonar_issues:
            context += f"- {issue['message']} (Severity: {issue['severity']})\n"

        # 3. Intent Inference & Risk (LLM)
        system_prompt = "You are a senior code reviewer. Analyze the diffs and static analysis issues."
        review = await self.llm.generate_response(system_prompt, context)

        print("[Reviewer] Review complete.")
        return review
