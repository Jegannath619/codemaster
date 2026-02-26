from typing import List, Dict, Any
from src.db.connector import MongoDBConnector

class KnowledgeBase:
    """
    Manages code chunking and retrieval (Simulated Vector Store).
    """
    def __init__(self, mongo: MongoDBConnector):
        self.mongo = mongo

    async def ingest_service(self, project_id: str, service_name: str, code_files: Dict[str, str]):
        """
        Chunks and stores code files for a service.
        """
        chunks = []
        for filepath, content in code_files.items():
            # Naive chunking: split by double newlines (paragraphs/functions)
            file_chunks = content.split('\n\n')
            for i, chunk_text in enumerate(file_chunks):
                if len(chunk_text.strip()) > 20: # Ignore tiny chunks
                    chunks.append({
                        "project_id": project_id,
                        "service_name": service_name,
                        "filepath": filepath,
                        "chunk_index": i,
                        "content": chunk_text,
                        "vector": [] # Placeholder for embedding
                    })

        # Store in Mongo (simulating vector DB insertion)
        for chunk in chunks:
            await self.mongo.mcp_manager.call_tool(
                "mongo",
                "insert_document",
                {"collection": "knowledge_base", "document": chunk}
            )

    async def retrieve_relevant_chunks(self, service_name: str, query: str = "", limit: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves relevant code chunks for a service.
        """
        # In a real RAG system, this would perform a vector similarity search.
        # Here, we just query by service name to simulate "fetching context".

        result = await self.mongo.mcp_manager.call_tool(
            "mongo",
            "find_documents",
            {
                "collection": "knowledge_base",
                "filter": {"service_name": service_name},
                "limit": limit
            }
        )

        if not isinstance(result, list):
            # Fallback mock data if DB is empty or mock returns simple status
            return [
                {
                    "service_name": service_name,
                    "filepath": "mock/file.cs",
                    "content": f"// Mock chunk from {service_name}\npublic void DoSomething() {{ ... }}"
                }
            ]

        return result
