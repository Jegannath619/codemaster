# Agentic AI Code Master - Design Document

## 1. Overview
The **Agentic AI Code Master** is an intelligent agent designed to analyze microservices codebases (C#, Vue.js, JavaScript), perform code reviews, assess impact, and suggest changes. It leverages a **Graph-based Context Awareness** and **Hybrid RAG** approach to overcome the limitations of traditional RAG in distributed systems.

## 2. Architecture

The system follows a modular architecture:

```
+------------------+      +----------------+      +-------------------+
|  CLI Interface   | <--> |   Agent Core   | <--> |   LLM Provider    |
|   (main.py)      |      | (src/agent.py) |      | (src/llm/base.py) |
+------------------+      +-------+--------+      +-------------------+
                                  |
                                  v
                        +--------------------+
                        |   Analysis Engine  |
                        | (src/analysis/*)   |
                        |     (src/rag/*)    |
                        +---------+----------+
                                  |
            +---------------------+---------------------+
            |                     |                     |
    +-------v-------+     +-------v-------+     +-------v-------+
    | GitLab Client |     | Mongo Client  |     |  Local FS     |
    | (src/gitlab/) |     | (src/db/)     |     | (src/utils/)  |
    +---------------+     +---------------+     +---------------+
```

### 2.1 Core Components

*   **Agent Core (`src/agent.py`)**: The central orchestrator. It receives user intents (e.g., "Review this PR"), plans the execution steps, invokes analysis tools, and synthesizes the final response using the LLM.
*   **LLM Abstraction (`src/llm/`)**: A flexible interface to switch between models (OpenAI, Anthropic, Local).
*   **MCP Client Manager (`src/mcp/`)**: Manages connections to MCP servers (GitLab, Mongo).

### 2.2 Analysis Engine ("Graph RAG")

To address the "microservices" challenge, we combine **Graph Awareness** with **Hybrid Search**.

*   **Dependency Graph Builder (`src/analysis/dependency_graph.py`)**:
    *   **Static Linking**: Parses `package.json`, `.csproj` for package references.
    *   **Dynamic Linking**: Parses `appsettings.json`, `.env` to find runtime service URLs/connection strings.
    *   Maps service-to-service relationships (e.g., Service A calls Service B via HTTP).

### 2.3 RAG Pipeline (`src/rag/`)

This module manages the "Indexing (Offline)" and "Querying (Runtime)" phases.

*   **Indexer (`src/rag/indexer.py`)**:
    *   **Code-Specific Parsing**: Uses regex-based parsing (simulating Tree-sitter) to identify function and class boundaries in C# and JS/TS.
    *   **Chunking**: Breaks files into logical units (e.g., individual methods or classes) rather than arbitrary text blocks.
    *   **Embedding**: Generates vector embeddings for each chunk (simulated).
    *   **Storage**: Stores chunks in MongoDB with rich metadata (function name, file path, service).

*   **Retriever (`src/rag/retriever.py`)**:
    *   **Hybrid Search**: Combines:
        1.  **Metadata Filtering**: Retrieve chunks ONLY from dependent services identified by the Graph Builder.
        2.  **Keyword Matching**: Filter chunks containing relevant function names or API endpoints.
        3.  **Semantic Search**: (Simulated) Vector similarity.
    *   **Context Assembly**: Integrates retrieved chunks into the LLM prompt.

## 3. Workflows

### 3.1 Code Review (Enhanced)
1.  **Trigger**: User requests review for a specific Merge Request (MR).
2.  **Analysis**:
    *   Fetch diffs from GitLab.
    *   **Graph Build**: Identify dependent services via `appsettings.json`.
    *   **Retrieve Context**:
        *   Query the RAG Retriever for chunks from dependent services matching the modified API signatures.
        *   Use Hybrid Search to find usage examples.
3.  **Review**:
    *   LLM analyzes the code with the full context (Graph + precise Code Chunks).
    *   Checks for logic errors, security flaws (cross-service), and style violations.
4.  **Output**: Structured review comments.

## 4. Configuration
Configuration is handled via environment variables (`.env`):
*   `GITLAB_API_URL`
*   `GITLAB_TOKEN`
*   `MONGODB_URI`
*   `LLM_API_KEY`
*   `LLM_MODEL`

## 5. Security & Principles
*   **Least Privilege**: Only request necessary scopes for GitLab/Mongo.
*   **Data Privacy**: Sensitive code is only sent to the configured LLM provider.
