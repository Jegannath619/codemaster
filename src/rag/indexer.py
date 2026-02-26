import re
from typing import List, Dict, Any
from src.db.connector import MongoDBConnector

class ASTDerivedIndexer:
    """
    Handles parsing, chunking, and embedding of code files using AST-derived logic.
    Simulates Tree-sitter behavior using regex to identify Classes, Interfaces, and Methods.
    """
    def __init__(self, mongo: MongoDBConnector):
        self.mongo = mongo

    async def ingest_service(self, project_id: str, service_name: str, code_files: Dict[str, str]):
        """
        Parses code files into semantic AST nodes and stores them.
        """
        nodes = []
        for filepath, content in code_files.items():
            file_nodes = self._parse_file(filepath, content)
            for i, node_data in enumerate(file_nodes):
                # Enrich with metadata
                node_data.update({
                    "project_id": project_id,
                    "service_name": service_name,
                    "filepath": filepath,
                    "node_index": i,
                    "vector": self._create_embedding(node_data["content"])
                })
                nodes.append(node_data)

        # Store in Mongo
        for node in nodes:
            await self.mongo.mcp_manager.call_tool(
                "mongo",
                "insert_document",
                {"collection": "rag_chunks", "document": node}
            )

    async def ingest_changes(self, project_id: str, service_name: str, code_files: Dict[str, str]):
        """
        Incrementally updates the index for the changed files.
        Inspired by CocoIndex strategies.
        """
        # 1. Delete old chunks for these files
        for filepath in code_files.keys():
            await self.mongo.mcp_manager.call_tool(
                "mongo",
                "delete_documents",
                {
                    "collection": "rag_chunks",
                    "filter": {"project_id": project_id, "service_name": service_name, "filepath": filepath}
                }
            )

        # 2. Ingest new content
        await self.ingest_service(project_id, service_name, code_files)


    def _parse_file(self, filepath: str, content: str) -> List[Dict[str, Any]]:
        """
        Splits file content into AST nodes.
        """
        if filepath.endswith(".cs"):
            return self._parse_csharp(content)
        elif filepath.endswith(".js") or filepath.endswith(".ts") or filepath.endswith(".vue"):
            return self._parse_javascript(content)
        else:
            return [{"type": "text", "name": "block", "content": c} for c in content.split('\n\n') if len(c.strip()) > 20]

    def _parse_csharp(self, content: str) -> List[Dict[str, Any]]:
        """
        Extracts C# Classes, Interfaces, and Methods.
        """
        nodes = []
        lines = content.split('\n')

        # 1. Class/Interface Definition
        # public class OrderService : IOrderService
        class_pattern = re.compile(r'(public|internal)\s+(class|interface)\s+(\w+)\s*(?::\s*([\w, ]+))?')

        # 2. Method Definition
        method_pattern = re.compile(r'(public|private|protected|internal)\s+[\w<>]+\s+(\w+)\s*\(.*?\)\s*\{')

        current_node = []
        current_name = "unknown"
        current_type = "unknown"
        in_block = False
        brace_count = 0

        for line in lines:
            # Check for Class/Interface start
            class_match = class_pattern.search(line)
            if class_match and not in_block:
                implements = class_match.group(4)
                if implements:
                    implements = implements.strip()

                nodes.append({
                    "type": class_match.group(2), # class or interface
                    "name": class_match.group(3),
                    "implements": implements if implements else "",
                    "content": line # Just the definition line for the high-level node
                })
                # We don't block-capture classes entirely to avoid huge chunks,
                # instead we capture methods inside them as separate nodes.

            if not in_block:
                method_match = method_pattern.search(line)
                if method_match:
                    in_block = True
                    current_type = "method"
                    current_name = method_match.group(2)
                    current_node = [line]
                    brace_count = line.count('{') - line.count('}')
            else:
                current_node.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    in_block = False
                    nodes.append({
                        "type": current_type,
                        "name": current_name,
                        "content": "\n".join(current_node)
                    })
                    current_node = []

        return nodes

    def _parse_javascript(self, content: str) -> List[Dict[str, Any]]:
        """
        Extracts JS functions and Classes.
        """
        nodes = []
        function_pattern = re.compile(r'(function\s+(\w+)|const\s+(\w+)\s*=\s*(\(.*?\)|async\s*\(.*?\))\s*=>)')
        class_pattern = re.compile(r'class\s+(\w+)')

        lines = content.split('\n')
        current_node = []
        current_name = "unknown"
        in_block = False
        brace_count = 0

        for line in lines:
            if not in_block:
                # Check for Class
                class_match = class_pattern.search(line)
                if class_match:
                    nodes.append({"type": "class", "name": class_match.group(1), "content": line})

                func_match = function_pattern.search(line)
                if func_match:
                    in_block = True
                    current_name = func_match.group(2) or func_match.group(3)
                    current_node = [line]
                    brace_count = line.count('{') - line.count('}')
                    if "=>" in line and "{" not in line:
                         nodes.append({"type": "function", "name": current_name, "content": line})
                         in_block = False
                         current_node = []
            else:
                current_node.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    in_block = False
                    nodes.append({
                        "type": "function",
                        "name": current_name,
                        "content": "\n".join(current_node)
                    })
                    current_node = []

        return nodes

    def _create_embedding(self, text: str) -> List[float]:
        """
        Creates a vector embedding for the text.
        """
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [float((hash_val >> i) & 0xFF) / 255.0 for i in range(0, 50, 10)]
