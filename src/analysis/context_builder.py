from typing import Dict, List, Any
from src.analysis.dependency_graph import DependencyGraphBuilder
from src.rag.retriever import HybridRetriever
from src.gitlab.connector import GitLabConnector

class ContextBuilder:
    """
    Constructs the prompt context for the LLM, integrating dependency information and Hybrid RAG chunks.
    """
    def __init__(self, gitlab: GitLabConnector, graph_builder: DependencyGraphBuilder, retriever: HybridRetriever):
        self.gitlab = gitlab
        self.graph_builder = graph_builder
        self.retriever = retriever

    async def build_context(self, project_id: str, mr_iid: int) -> str:
        """
        Builds the context string for a given Merge Request using Graph RAG + Hybrid Search.
        """
        # 1. Fetch changed files (diffs)
        diffs = await self.gitlab.get_merge_request_diffs(project_id, mr_iid)

        # 2. Extract touched files
        changed_filepaths = [d['new_path'] for d in diffs]

        # 3. Build dependency graph for affected services
        # This tells us which services might be impacted or are dependencies.
        dependency_map = await self.graph_builder.build_graph(project_id, changed_filepaths)

        # 4. Construct the context prompt
        context = "### Code Review Context (Graph RAG Enhanced) ###\n\n"
        context += "You are an expert software engineer reviewing a Merge Request in a microservices architecture.\n"
        context += "Your goal is to identify logic errors, security flaws, and cross-service integration issues.\n\n"

        context += "### Affected Services & Dependencies ###\n"
        for service, deps in dependency_map.items():
            context += f"- Service: {service}\n"
            context += f"  Dependencies: {', '.join(deps)}\n"

            # --- RAG PIPELINE: Fetch relevant chunks via Hybrid Retriever ---
            for dep in deps:
                # We use the dependency name as a keyword query (heuristic)
                # In a smarter agent, we'd extract specific API calls from the diff (e.g., 'POST /api/orders')
                # and use that as the query.
                query = f"{dep} API contract"

                chunks = await self.retriever.search(service_name=dep, query=query, limit=2)

                if chunks:
                    context += f"  - [Hybrid RAG] Context from {dep}:\n"
                    for chunk in chunks:
                        # Improved context formatting
                        chunk_type = chunk.get("type", "code")
                        name = chunk.get("name", "unknown")
                        content_snippet = chunk.get('content', '')[:500] # Increased limit for better context
                        context += f"    * ({chunk_type}) {name}:\n      ```\n{content_snippet}\n      ```\n"

        context += "\n"

        context += "### Changes ###\n"
        for diff in diffs:
            context += f"File: {diff['new_path']}\n"
            context += f"```diff\n{diff['diff']}\n```\n\n"

        return context
