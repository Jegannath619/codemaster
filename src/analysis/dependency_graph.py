import json
import re
from typing import Dict, List, Set, Any
from src.gitlab.connector import GitLabConnector

class DeterministicGraphBuilder:
    """
    Builds a Deterministic AST-Derived Knowledge Graph (DKB) for microservices.
    Simulates the Tree-sitter traversal described in arXiv:2601.08773.
    """
    def __init__(self, gitlab: GitLabConnector):
        self.gitlab = gitlab

    async def build_graph(self, project_id: str, files: List[str]) -> Dict[str, List[str]]:
        """
        Analyzes the given files to find dependencies and builds a graph.
        Focuses on 'Controller -> Service -> Repo' chains.

        Returns:
            A dictionary where keys are service names and values are lists of dependencies.
        """
        graph: Dict[str, List[str]] = {}

        for file in files:
            service_name = self._extract_service_name(file)
            if service_name and service_name not in graph:
                # Get base dependencies (packages, config)
                dependencies = await self._analyze_service_dependencies(project_id, service_name, file)

                # ENHANCEMENT: Analyze Code for Internal Chains (Controller -> Service)
                if file.endswith("Controller.cs"):
                    internal_deps = await self._analyze_controller_injections(project_id, file)
                    dependencies.extend(internal_deps)

                graph[service_name] = list(set(dependencies))

        return graph

    def _extract_service_name(self, filepath: str) -> str:
        parts = filepath.split('/')
        if len(parts) > 1 and parts[0] == "src":
            return parts[1] # e.g., src/ServiceA/..
        return "UnknownService"

    async def _analyze_service_dependencies(self, project_id: str, service_name: str, filepath: str) -> List[str]:
        dependencies = set()

        # 1. Static Linking (.csproj)
        csproj_path = f"src/{service_name}/{service_name}.csproj"
        try:
            content = await self.gitlab.get_file_content(project_id, csproj_path)
            if content:
                matches = re.findall(r'Include="([^"]+)"', content)
                for match in matches:
                    if "Service" in match or "Client" in match:
                        dependencies.add(match)
        except Exception:
            pass

        # 2. Static Linking (package.json)
        package_json_path = f"src/{service_name}/package.json"
        try:
            content = await self.gitlab.get_file_content(project_id, package_json_path)
            if content:
                data = json.loads(content)
                deps = data.get("dependencies", {})
                for dep in deps:
                    if "service" in dep or "client" in dep:
                        dependencies.add(dep)
        except Exception:
            pass

        # 3. Dynamic Linking (appsettings.json)
        appsettings_path = f"src/{service_name}/appsettings.json"
        try:
            content = await self.gitlab.get_file_content(project_id, appsettings_path)
            if content:
                config_deps = self._parse_appsettings_dependencies(content)
                dependencies.update(config_deps)
        except Exception:
            pass

        return list(dependencies)

    async def _analyze_controller_injections(self, project_id: str, filepath: str) -> List[str]:
        """
        Analyzes a Controller file to find injected services (Simulation of DKB Traversal).
        """
        deps = []
        try:
            content = await self.gitlab.get_file_content(project_id, filepath)
            if content:
                # Heuristic: Find private readonly fields usually injected via constructor
                # private readonly IOrderService _orderService;
                matches = re.findall(r'private\s+readonly\s+(I[A-Z]\w+)\s+_(\w+);', content)
                for match in matches:
                    interface_name = match[0] # e.g. IOrderService
                    # In a full DKB, we would resolve 'IOrderService' to its implementation.
                    # Here we just add it as a node dependency.
                    deps.append(interface_name)
        except Exception:
            pass
        return deps

    def _parse_appsettings_dependencies(self, content: str) -> Set[str]:
        """
        Parses appsettings.json content to find service dependencies.
        """
        deps = set()
        try:
            data = json.loads(content)

            def search_dict(d):
                for key, value in d.items():
                    if isinstance(value, dict):
                        search_dict(value)
                    elif isinstance(value, str):
                        if "http" in value and ("service" in value.lower() or "api" in value.lower()):
                            match = re.search(r'https?://([^:/]+)', value)
                            if match:
                                deps.add(match.group(1))

                    if "ConnectionStrings" in key or "ConnectionString" in key:
                        pass # handled by value check below

                    # Check current level keys for connection strings
                    if isinstance(value, str):
                        if "mongodb://" in value:
                            deps.add("MongoDB")
                        if "Server=" in value and "Database=" in value:
                            deps.add("SQLServer")

            search_dict(data)
        except json.JSONDecodeError:
            pass

        return deps
