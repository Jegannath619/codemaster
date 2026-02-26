import json
import re
from typing import Dict, List, Set, Any
from src.gitlab.connector import GitLabConnector

class DependencyGraphBuilder:
    """
    Builds a dependency graph for microservices by analyzing project files.
    """
    def __init__(self, gitlab: GitLabConnector):
        self.gitlab = gitlab

    async def build_graph(self, project_id: str, files: List[str]) -> Dict[str, List[str]]:
        """
        Analyzes the given files to find dependencies and builds a graph.

        Returns:
            A dictionary where keys are service names and values are lists of dependencies.
        """
        graph: Dict[str, List[str]] = {}

        # In a real scenario, we would scan the entire repo.
        # Here we check if the changed files belong to a service that has a project file.

        # Mocking logic: infer service name from file path
        # src/ServiceA/Controllers/... -> ServiceA

        for file in files:
            service_name = self._extract_service_name(file)
            if service_name and service_name not in graph:
                dependencies = await self._analyze_service_dependencies(project_id, service_name, file)
                graph[service_name] = dependencies

        return graph

    def _extract_service_name(self, filepath: str) -> str:
        parts = filepath.split('/')
        if len(parts) > 1 and parts[0] == "src":
            return parts[1] # e.g., src/ServiceA/..
        return "UnknownService"

    async def _analyze_service_dependencies(self, project_id: str, service_name: str, filepath: str) -> List[str]:
        dependencies = []

        # Check for C# Project file
        # We assume standard structure: src/ServiceA/ServiceA.csproj
        csproj_path = f"src/{service_name}/{service_name}.csproj"
        try:
            content = await self.gitlab.get_file_content(project_id, csproj_path)
            if content:
                # Simple regex to find package references or project references
                # <PackageReference Include="ServiceB.Client" ... />
                matches = re.findall(r'Include="([^"]+)"', content)
                for match in matches:
                    if "Service" in match or "Client" in match:
                        dependencies.append(match)
        except Exception:
            pass # File might not exist

        # Check for Node.js package.json
        package_json_path = f"src/{service_name}/package.json"
        try:
            content = await self.gitlab.get_file_content(project_id, package_json_path)
            if content:
                data = json.loads(content)
                deps = data.get("dependencies", {})
                for dep in deps:
                    if "service" in dep or "client" in dep:
                        dependencies.append(dep)
        except Exception:
            pass

        return list(set(dependencies))
