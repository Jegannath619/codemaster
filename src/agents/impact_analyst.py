from typing import Dict, Any
from src.llm.base import LLMProvider
from src.gitlab.connector import GitLabConnector
from src.rag.retriever import HybridRetriever
from src.dynatrace.connector import DynatraceConnector

class ImpactAnalystAgent:
    """
    Agent responsible for Impact Analysis.
    Combines Static Graph (DKB) with Runtime Topology (Dynatrace).
    """
    def __init__(self, llm: LLMProvider, gitlab: GitLabConnector, retriever: HybridRetriever, dynatrace: DynatraceConnector):
        self.llm = llm
        self.gitlab = gitlab
        self.retriever = retriever
        self.dynatrace = dynatrace

    async def analyze_impact(self, project_id: str, service_name: str) -> str:
        print(f"[ImpactAnalyst] Analyzing service: {service_name}")

        # 1. Static Analysis (DKB/RAG)
        # In a real impl, we'd traverse the DKB here.
        # For now, we use the retriever to get relevant chunks.
        chunks = await self.retriever.search(service_name, "API contract")

        # 2. Runtime Analysis (Dynatrace)
        topology = await self.dynatrace.get_service_dependencies(service_name)
        metrics = await self.dynatrace.get_service_metrics(service_name)

        # 3. Synthesize Report
        report = f"Impact Analysis for {service_name}:\n"
        report += f"- Static Dependencies: Found {len(chunks)} relevant code modules.\n"
        report += f"- Runtime Consumers: {', '.join(topology.get('callers', []))}\n"
        report += f"- Current Traffic: {metrics.get('requests_per_min', 0)} rpm\n"

        if metrics.get('error_rate', 0) > 0.01:
            report += "⚠️ WARNING: Service has elevated error rates. Proceed with caution.\n"

        return report
