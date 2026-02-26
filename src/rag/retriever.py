from typing import List, Dict, Any
from src.db.connector import MongoDBConnector

class HybridRetriever:
    """
    Retrieves code chunks using a hybrid approach (Semantic + Keyword + Metadata).
    """
    def __init__(self, mongo: MongoDBConnector):
        self.mongo = mongo

    async def search(self, service_name: str, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Performs a hybrid search.

        Args:
            service_name: The service to search within (Metadata Filter).
            query: The search query (used for Keyword matching and Vector sim).
            limit: Max results.
        """
        # In a real system (e.g., Mongo Atlas Search or Pinecone):
        # We would construct a query combining:
        # 1. $filter: { service_name: service_name }
        # 2. $search: { text: { query: query, path: "content" } }
        # 3. $vectorSearch: { queryVector: embed(query), ... }

        # Here, we simulate this by fetching by service name and filtering in memory.

        # 1. Metadata Filter (Service Name)
        candidates = await self.mongo.mcp_manager.call_tool(
            "mongo",
            "find_documents",
            {
                "collection": "rag_chunks",
                "filter": {"service_name": service_name},
                "limit": 50 # Fetch more candidates for in-memory ranking
            }
        )

        if not isinstance(candidates, list) or not candidates:
            # Return mock if empty
            return [
                 {
                    "service_name": service_name,
                    "name": "ProcessPayment",
                    "type": "method",
                    "content": f"// Mock result from {service_name}\npublic void ProcessPayment() {{ ... }}",
                    "score": 0.9
                }
            ]

        # 2. Keyword / "Hybrid" Ranking
        scored_results = []
        query_terms = set(query.lower().split())

        for doc in candidates:
            content = doc.get("content", "").lower()
            name = doc.get("name", "").lower()

            score = 0
            # Simple keyword scoring
            for term in query_terms:
                if term in name:
                    score += 10 # High boost for function name match
                if term in content:
                    score += 1

            # Simulate semantic score (random or mock)
            # In real life: score += vector_cosine_similarity(doc['vector'], query_vector)
            score += 0.5

            if score > 0:
                doc["score"] = score
                scored_results.append(doc)

        # Sort by score desc
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        return scored_results[:limit]
