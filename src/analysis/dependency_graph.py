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
        dependencies = set()

        # 1. Check for C# Project file (.csproj)
        csproj_path = f"src/{service_name}/{service_name}.csproj"
        try:
            content = await self.gitlab.get_file_content(project_id, csproj_path)
            if content:
                matches = re.findall(r'Include="([^"]+)"', content)
                for match in matches:
                    if "Service" in match or "Client" in match:
                        dependencies.add(match)
        except Exception:
            pass # File might not exist

        # 2. Check for Node.js package.json
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

        # 3. Check for Configuration Files (appsettings.json)
        # This allows dynamic linking based on URLs or connection strings found in config.
        appsettings_path = f"src/{service_name}/appsettings.json"
        try:
            content = await self.gitlab.get_file_content(project_id, appsettings_path)
            if content:
                config_deps = self._parse_appsettings_dependencies(content)
                dependencies.update(config_deps)
        except Exception:
            pass

        return list(dependencies)

    def _parse_appsettings_dependencies(self, content: str) -> Set[str]:
        """
        Parses appsettings.json content to find service dependencies.
        """
        deps = set()
        try:
            data = json.loads(content)

            # recursive search for keys that look like service URLs
            def search_dict(d):
                for key, value in d.items():
                    if isinstance(value, dict):
                        search_dict(value)
                    elif isinstance(value, str):
                        # Heuristic: Check for URLs or specific naming conventions
                        if "http" in value and ("service" in value.lower() or "api" in value.lower()):
                            # Extract service name from URL (simplified)
                            # e.g., "http://service-b:8080" -> "service-b"
                            match = re.search(r'https?://([^:/]+)', value)
                            if match:
                                deps.add(match.group(1))

                    if "ConnectionStrings" in key or "ConnectionString" in key:
                        # Value might be a string (simple connection string) or nested object in some configs
                        # but usually key is 'ConnectionStrings' and value is dict of names.
                        # Here 'value' is passed as the 'search_dict' argument's value, which can be the string itself.
                        # However, our recursive loop 'search_dict(d)' iterates keys/values.
                        # When d={'ConnectionStrings': {'MainDb': '...'}}, key='ConnectionStrings', value={'MainDb': '...'}
                        # The recursive call search_dict({'MainDb': '...'}) will happen.
                        pass

                # Check current level keys for connection strings if we are inside a 'ConnectionStrings' block (hard to track state recursively simply).
                # Simplified check: if any string value looks like a connection string.
                if isinstance(value, str):
                    if "mongodb://" in value:
                        deps.add("MongoDB")
                    if "Server=" in value and "Database=" in value:
                        deps.add("SQLServer")

            search_dict(data)
        except json.JSONDecodeError:
            pass

        return deps
