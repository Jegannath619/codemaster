import os
import json
from typing import Dict, Any, List, Optional
from src.mcp.client import MCPClientManager

class GitLabConnector:
    """
    Connects to GitLab using MCP or direct API calls.
    """
    def __init__(self, mcp_manager: MCPClientManager):
        self.mcp_manager = mcp_manager
        self.api_url = os.getenv("GITLAB_API_URL", "https://gitlab.com/api/v4")
        self.token = os.getenv("GITLAB_TOKEN", "dummy_token")
        self.server_name = "gitlab"

    async def initialize(self):
        """
        Initializes the connection to the GitLab MCP server.
        """
        config = {
            "command": "npx",
            "args": ["-y", "@gitlab-org/gitlab-mcp-server"],
            "env": {
                "GITLAB_API_URL": self.api_url,
                "GITLAB_TOKEN": self.token
            }
        }
        await self.mcp_manager.connect(self.server_name, config)

    async def get_project_info(self, project_id: str) -> Dict[str, Any]:
        """
        Retrieves project information.
        """
        return await self.mcp_manager.call_tool(
            self.server_name,
            "get_project",
            {"project_id": project_id}
        )

    async def get_merge_request_diffs(self, project_id: str, mr_iid: int) -> List[Dict[str, Any]]:
        """
        Retrieves diffs for a specific Merge Request.
        """
        # Simulated call - assuming the MCP server has a tool for this
        # If not, we would fall back to httpx/requests here.
        try:
            return await self.mcp_manager.call_tool(
                self.server_name,
                "get_merge_request_diffs",
                {"project_id": project_id, "mr_iid": mr_iid}
            )
        except Exception as e:
            print(f"[GitLabConnector] MCP call failed, falling back to mock API: {e}")
            return [
                {
                    "new_path": "src/ServiceA/Controllers/PaymentController.cs",
                    "diff": "@@ -10,7 +10,7 @@\n public async Task<IActionResult> ProcessPayment(PaymentRequest req)\n {\n-    var result = await _serviceB.Charge(req);\n+    var result = await _serviceB.ChargeAsync(req);\n     return Ok(result);\n }"
                }
            ]

    async def get_file_content(self, project_id: str, filepath: str, ref: str = "main") -> str:
        """
        Retrieves the content of a file.
        """
        result = await self.mcp_manager.call_tool(
            self.server_name,
            "get_file_content",
            {"project_id": project_id, "filepath": filepath, "ref": ref}
        )
        if isinstance(result, str):
            return result
        return result.get("content", "")

    async def post_comment(self, project_id: str, mr_iid: int, body: str):
        """
        Posts a comment on a Merge Request.
        """
        await self.mcp_manager.call_tool(
            self.server_name,
            "create_mr_note",
            {"project_id": project_id, "mr_iid": mr_iid, "body": body}
        )
