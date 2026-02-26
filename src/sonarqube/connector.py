import os
from typing import List, Dict, Any

class SonarQubeConnector:
    """
    Mock connector for SonarQube.
    """
    def __init__(self):
        self.url = os.getenv("SONAR_HOST_URL", "http://sonar.example.com")
        self.token = os.getenv("SONAR_TOKEN", "dummy")

    async def get_issues_for_project(self, project_key: str) -> List[Dict[str, Any]]:
        """
        Fetches open issues for a project.
        """
        # Mock response
        return [
            {"message": "Remove this unused private field.", "severity": "MINOR", "file": "src/ServiceA/Order.cs"},
            {"message": "Refactor this method to reduce cognitive complexity.", "severity": "MAJOR", "file": "src/ServiceA/OrderController.cs"}
        ]
