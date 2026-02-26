import os
from typing import Dict, Any, List, Optional
from src.mcp.client import MCPClientManager

class MongoDBConnector:
    """
    Connects to MongoDB using MCP.
    """
    def __init__(self, mcp_manager: MCPClientManager):
        self.mcp_manager = mcp_manager
        self.mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.server_name = "mongo"

    async def initialize(self):
        """
        Initializes the connection to the MongoDB MCP server.
        """
        config = {
            "command": "node",
            "args": ["path/to/mcp-mongo-server.js"],
            "env": {
                "MONGODB_URI": self.mongo_uri
            }
        }
        await self.mcp_manager.connect(self.server_name, config)

    async def save_analysis(self, project_id: str, mr_iid: int, analysis_result: Dict[str, Any]):
        """
        Saves the analysis result to MongoDB.
        """
        document = {
            "project_id": project_id,
            "mr_iid": mr_iid,
            "analysis": analysis_result,
            "timestamp": "2024-10-27T12:00:00Z" # In real app, use datetime.now()
        }
        await self.mcp_manager.call_tool(
            self.server_name,
            "insert_document",
            {"collection": "code_reviews", "document": document}
        )

    async def get_previous_reviews(self, project_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves previous reviews for a project.
        """
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "find_documents",
            {"collection": "code_reviews", "filter": {"project_id": project_id}, "limit": limit}
        )
        # Mock return if result is None (since our mock client returns basic dicts)
        if not isinstance(result, list):
            return []
        return result
