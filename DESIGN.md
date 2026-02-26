# Agentic AI Code Master - Design Document

## 1. Overview
The **Agentic AI Code Master** is an intelligent agent designed to analyze microservices codebases (C#, Vue.js, JavaScript), perform code reviews, assess impact, and suggest changes. It implements a **Deterministic AST-Derived Knowledge Graph (DKB)** approach (inspired by **arXiv:2601.08773**) and **Real-Time Codebase Indexing** (validated by **CocoIndex**) to provide superior reliability, speed, and coverage compared to traditional RAG or LLM-based Knowledge Graphs (LLM-KB).

## 2. Architecture

The system follows a modular architecture:

```
+------------------+      +----------------+      +-------------------+
|  CLI Interface   | <--> |   Agent Core   | <--> |   LLM Provider    |
|   (main.py)      |      | (src/agent.py) |      | (src/llm/base.py) |
+------------------+      +-------+--------+      +-------------------+
                                  ^
                                  |
                        +--------------------+
                        |   Webhook Server   |  <-- GitLab Webhooks
                        | (src/webhook_server.py) |
                        +--------------------+
```

### 2.1 Core Components

*   **Agent Core (`src/agent.py`)**: The central orchestrator. It receives user intents (e.g., "Review this PR"), plans the execution steps, invokes analysis tools, and synthesizes the final response using the LLM.
*   **Webhook Server (`src/webhook_server.py`)**: A FastAPI service that listens for GitLab events (Push, Merge Request) to trigger real-time actions.
*   **LLM Abstraction (`src/llm/`)**: A flexible interface to switch between models (OpenAI, Anthropic, Local).
*   **MCP Client Manager (`src/mcp/`)**: Manages connections to MCP servers (GitLab, Mongo).

### 2.2 Analysis Engine ("DKB - Reliable Graph RAG")

As demonstrated in **arXiv:2601.08773**, deterministic graph construction outperforms LLM-based extraction. We implement:

*   **Deterministic Graph Builder (`src/analysis/dependency_graph.py`)**:
    *   **Logic**: Uses Tree-sitter (simulated via strict Regex) to build an AST-derived graph.
    *   **Graph Schema**: `Controller` -> `Service` -> `Repository` -> `Interface`.
    *   **Bidirectional Traversal**: Supports finding both dependencies (downstream) and usages (upstream) for Impact Analysis.
    *   **Dynamic Linking**: Parses `appsettings.json`, `.env` to link services at runtime.

### 2.3 RAG Pipeline (`src/rag/`)

This module manages the "Indexing (Offline)" and "Querying (Runtime)" phases, enhanced with **CocoIndex-style Incremental Updates**.

*   **AST-Derived Indexer (`src/rag/indexer.py`)**:
    *   **Code-Specific Parsing**: Identifies semantic units: Classes, Interfaces, Methods.
    *   **Relationships**: Captures `Implements` and `Extends` relationships.
    *   **Chunking**: Breaks files into logical AST nodes rather than arbitrary text blocks.
    *   **Incremental Indexing**: When a PR is created or code is pushed, only the changed files are re-indexed. Old chunks for these files are deleted, and new AST nodes are inserted. This ensures real-time index freshness.
    *   **Embedding**: Generates vector embeddings for each node.
    *   **Storage**: Stores nodes in MongoDB with rich metadata (type, name, file path, service).

*   **Retriever (`src/rag/retriever.py`)**:
    *   **Hybrid Search**: Combines:
        1.  **Graph Traversal**: Follow the DKB edges (e.g., given a Controller change, traverse to its Service and Repository).
        2.  **Keyword Matching**: Filter chunks containing relevant function names or API endpoints.
        3.  **Semantic Search**: Vector similarity.
    *   **Context Assembly**: Integrates retrieved chunks into the LLM prompt.

## 3. Workflows

### 3.1 Real-Time Code Indexing (Webhook)
1.  **Trigger**: GitLab Push Event (Developer commits code).
2.  **Action**: Webhook Server receives payload.
3.  **Indexing**:
    *   Extract modified files from the payload.
    *   Call `Agent.ingest_changes(project_id, service_name, files)`.
    *   Agent updates the RAG Index incrementally (Delete Old -> Insert New).

### 3.2 Code Review (Enhanced with DKB)
1.  **Trigger**: User requests review for a specific Merge Request (MR) or via Webhook (MR Event).
2.  **Analysis**:
    *   Fetch diffs from GitLab.
    *   **Incremental Update**: Ensure index is fresh.
    *   **Graph Build**: Identify affected `Controller` or `Service` nodes.
    *   **Traverse Graph**: Find dependent `Repository` or `Interface` definitions using the deterministic graph.
    *   **Retrieve Context**: Fetch the code for these specific nodes.
3.  **Review**:
    *   LLM analyzes the code with the full context (Graph Nodes + precise Code Chunks).
    *   Checks for logic errors, security flaws (cross-service), and style violations.
4.  **Output**: Structured review comments.

### 3.3 Impact Analysis (Bidirectional)
1.  **Trigger**: User proposes a change to a specific service/API.
2.  **Analysis**:
    *   Identify the target node (Service/Interface).
    *   **Reverse Traverse**: Find all `Controller`s or `Client`s that depend on this node.
    *   Fetch usage examples from dependent services.
3.  **Report**:
    *   List potentially broken services.
    *   Highlight necessary updates in consumers.

### 3.4 Suggest Changes
1.  **Trigger**: "Refactor Service A to use the new Auth API".
2.  **Execution**:
    *   Agent identifies all call sites using the DKB.
    *   Generates code patches for each occurrence.
    *   Verifies syntax (basic check).
3.  **Output**: Git patch or new MR.

## 4. Configuration
Configuration is handled via environment variables (`.env`):
*   `GITLAB_API_URL`
*   `GITLAB_TOKEN`
*   `MONGODB_URI`
*   `LLM_API_KEY`
*   `LLM_MODEL`
*   `WEBHOOK_SECRET` (for verifying GitLab payloads)

## 5. Security & Principles
*   **Least Privilege**: Only request necessary scopes for GitLab/Mongo.
*   **Data Privacy**: Sensitive code is only sent to the configured LLM provider.
