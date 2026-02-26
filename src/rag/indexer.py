import re
from typing import List, Dict, Any
from src.db.connector import MongoDBConnector

class CodeIndexer:
    """
    Handles parsing, chunking, and embedding of code files.
    """
    def __init__(self, mongo: MongoDBConnector):
        self.mongo = mongo

    async def ingest_service(self, project_id: str, service_name: str, code_files: Dict[str, str]):
        """
        Parses code files into semantic chunks and stores them.
        """
        chunks = []
        for filepath, content in code_files.items():
            file_chunks = self._chunk_file(filepath, content)
            for i, chunk_data in enumerate(file_chunks):
                # Enrich with metadata
                chunk_data.update({
                    "project_id": project_id,
                    "service_name": service_name,
                    "filepath": filepath,
                    "chunk_index": i,
                    "vector": self._create_embedding(chunk_data["content"])
                })
                chunks.append(chunk_data)

        # Store in Mongo
        for chunk in chunks:
            await self.mongo.mcp_manager.call_tool(
                "mongo",
                "insert_document",
                {"collection": "rag_chunks", "document": chunk}
            )

    def _chunk_file(self, filepath: str, content: str) -> List[Dict[str, Any]]:
        """
        Splits file content into logical units (functions/classes) based on file extension.
        Simulates Tree-sitter behavior using regex.
        """
        if filepath.endswith(".cs"):
            return self._parse_csharp(content)
        elif filepath.endswith(".js") or filepath.endswith(".ts") or filepath.endswith(".vue"):
            return self._parse_javascript(content)
        else:
            # Fallback: Paragraph chunking
            return [{"type": "text", "name": "block", "content": c} for c in content.split('\n\n') if len(c.strip()) > 20]

    def _parse_csharp(self, content: str) -> List[Dict[str, Any]]:
        """
        Extracts C# methods using Regex.
        Matches: [access modifier] [return type] [MethodName](args) { ... }
        """
        chunks = []
        # Simplified regex for C# method signature.
        # Note: Balancing braces with regex is hard/impossible, this is a heuristic approximation.
        # We assume methods are separated by newlines and indentation is standard.
        method_pattern = re.compile(r'(public|private|protected|internal)\s+[\w<>]+\s+(\w+)\s*\(.*?\)\s*\{')

        lines = content.split('\n')
        current_chunk = []
        current_name = "unknown"
        in_method = False
        brace_count = 0

        for line in lines:
            if not in_method:
                match = method_pattern.search(line)
                if match:
                    in_method = True
                    current_name = match.group(2)
                    current_chunk = [line]
                    brace_count = line.count('{') - line.count('}')
                else:
                    # Keep accumulating class-level context or comments? For now, ignore.
                    pass
            else:
                current_chunk.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    in_method = False
                    chunks.append({
                        "type": "method",
                        "name": current_name,
                        "content": "\n".join(current_chunk)
                    })
                    current_chunk = []

        return chunks

    def _parse_javascript(self, content: str) -> List[Dict[str, Any]]:
        """
        Extracts JS functions.
        Matches: function name() or const name = () =>
        """
        chunks = []
        # Heuristic for JS/TS functions
        function_pattern = re.compile(r'(function\s+(\w+)|const\s+(\w+)\s*=\s*(\(.*?\)|async\s*\(.*?\))\s*=>)')

        lines = content.split('\n')
        current_chunk = []
        current_name = "unknown"
        in_function = False
        brace_count = 0

        for line in lines:
            if not in_function:
                match = function_pattern.search(line)
                if match:
                    in_function = True
                    current_name = match.group(2) or match.group(3)
                    current_chunk = [line]
                    brace_count = line.count('{') - line.count('}')
                    # Single line arrow function check
                    if "=>" in line and "{" not in line:
                         chunks.append({"type": "function", "name": current_name, "content": line})
                         in_function = False
                         current_chunk = []
                else:
                    pass
            else:
                current_chunk.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    in_function = False
                    chunks.append({
                        "type": "function",
                        "name": current_name,
                        "content": "\n".join(current_chunk)
                    })
                    current_chunk = []

        return chunks

    def _create_embedding(self, text: str) -> List[float]:
        """
        Creates a vector embedding for the text.
        """
        # Mock embedding: deterministic hash-based vector for reproducibility in tests
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        # Create a tiny mock vector of size 5
        return [float((hash_val >> i) & 0xFF) / 255.0 for i in range(0, 50, 10)]
