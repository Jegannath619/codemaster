import os
from typing import List, Dict, Any

class DynatraceConnector:
    """
    Mock connector for Dynatrace.
    """
    def __init__(self):
        self.url = os.getenv("DYNATRACE_URL", "https://dt.example.com")
        self.token = os.getenv("DYNATRACE_TOKEN", "dummy")

    async def get_service_dependencies(self, service_id: str) -> Dict[str, List[str]]:
        """
        Returns runtime dependencies (callers/callees).
        """
        # Mock topology
        return {
            "callers": ["MobileApp", "WebFrontend"],
            "callees": ["PaymentService", "InventoryService"]
        }

    async def get_service_metrics(self, service_id: str) -> Dict[str, Any]:
        """
        Returns key metrics (traffic, errors).
        """
        return {
            "requests_per_min": 1500,
            "error_rate": 0.005, # 0.5%
            "apdex": 0.95
        }
