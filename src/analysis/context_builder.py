from typing import Dict, List, Any
from src.analysis.dependency_graph import DependencyGraphBuilder
from src.gitlab.connector import GitLabConnector

class ContextBuilder:
    """
    Constructs the prompt context for the LLM, integrating dependency information.
    """
    def __init__(self, gitlab: GitLabConnector, graph_builder: DependencyGraphBuilder):
        self.gitlab = gitlab
        self.graph_builder = graph_builder

    async def build_context(self, project_id: str, mr_iid: int) -> str:
        """
        Builds the context string for a given Merge Request.
        """
        # 1. Fetch changed files (diffs)
        diffs = await self.gitlab.get_merge_request_diffs(project_id, mr_iid)

        # 2. Extract touched files
        changed_filepaths = [d['new_path'] for d in diffs]

        # 3. Build dependency graph for affected services
        # This tells us which services might be impacted or are dependencies.
        dependency_map = await self.graph_builder.build_graph(project_id, changed_filepaths)

        # 4. Construct the context prompt
        context = "### Code Review Context ###\n\n"
        context += "You are an expert software engineer reviewing a Merge Request in a microservices architecture.\n"
        context += "Your goal is to identify logic errors, security flaws, and cross-service integration issues.\n\n"

        context += "### Affected Services & Dependencies ###\n"
        for service, deps in dependency_map.items():
            context += f"- Service: {service}\n"
            context += f"  Dependencies: {', '.join(deps)}\n"
        context += "\n"

        context += "### Changes ###\n"
        for diff in diffs:
            context += f"File: {diff['new_path']}\n"
            context += f"```diff\n{diff['diff']}\n```\n\n"

        # 5. (Optional) Fetch API Contracts of dependencies
        # In a full implementation, we would loop through 'deps' and fetch their OpenAPI specs.
        # context += "### API Contracts ###\n..."

        return context
