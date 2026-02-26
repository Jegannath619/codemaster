# Agentic AI Code Master - Design Document

## 1. Overview
The **Agentic AI Code Master** is an intelligent agent designed to analyze microservices codebases (C#, Vue.js, JavaScript), perform code reviews, assess impact, and suggest changes. It leverages a **Graph-based Context Awareness** approach to overcome the limitations of traditional RAG in distributed systems. It integrates with **GitLab** and **MongoDB** using the **Model Context Protocol (MCP)** or direct APIs where applicable.

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
    *   `LLMProvider`: Abstract base class.
    *   `OpenAIProvider`, `AnthropicProvider`: Concrete implementations.
*   **MCP Client Manager (`src/mcp/`)**: Manages connections to MCP servers.
    *   Standardizes tool discovery and execution for GitLab and MongoDB.
*   **GitLab Connector (`src/gitlab/`)**: Handles interactions with GitLab.
    *   Fetching code, merge requests, comments.
    *   Uses MCP if available, falls back to REST API.
    *   Reads `GITLAB_API_URL` and tokens from environment variables.
*   **MongoDB Connector (`src/db/`)**: Handles interactions with MongoDB.
    *   Stores analysis metadata, user preferences, and **Code Chunks (Knowledge Base)**.
    *   Uses MCP or direct driver.

### 2.2 Analysis Engine ("Graph RAG")

To address the "microservices" challenge, we move beyond simple text chunking by combining **Graph Awareness** with **Config-based Linking**.

*   **Dependency Graph Builder (`src/analysis/dependency_graph.py`)**:
    *   **Static Linking**: Parses `package.json`, `.csproj` for package references.
    *   **Dynamic Linking (Enhanced)**: Parses configuration files like `appsettings.json` (C#), `.env`, or `config.js` to find runtime dependencies (e.g., service URLs, connection strings).
    *   Maps service-to-service relationships (e.g., Service A calls Service B via HTTP).

*   **Knowledge Base / Chunking (`src/analysis/knowledge_base.py`)**:
    *   **Chunking Strategy**: Splits source code into semantic chunks (functions/classes).
    *   **Storage**: Stores chunks in MongoDB (simulated vector store) tagged by service name.
    *   **Retrieval**: Fetches relevant code snippets based on the dependency graph.

*   **Context Builder (`src/analysis/context_builder.py`)**:
    *   Constructs the prompt context intelligently.
    *   Instead of random chunks, it includes:
        *   The target file/change.
        *   **Linked Chunks**: Code from dependent services identified via `appsettings.json`.
        *   Relevant database schemas.

*   **Cross-Service Tracer (`src/analysis/tracer.py`)**:
    *   (Future/Mocked) Static analysis to trace API calls across repositories.

## 3. Workflows

### 3.1 Code Review
1.  **Trigger**: User requests review for a specific Merge Request (MR) or file.
2.  **Analysis**:
    *   Fetch diffs from GitLab.
    *   Identify touched files and services.
    *   **Graph Build**: Parse `appsettings.json` to find linked services.
    *   **Retrieve Context**: Fetch relevant chunks from the Knowledge Base for those linked services.
3.  **Review**:
    *   LLM analyzes the code with the full context (Graph + Chunks).
    *   Checks for logic errors, security flaws (cross-service), and style violations.
4.  **Output**: Structured review comments pushed to GitLab or displayed in CLI.

### 3.2 Impact Analysis
1.  **Trigger**: User proposes a change to a specific service/API.
2.  **Analysis**:
    *   Identify all services that consume the modified API (reverse dependency lookup via `appsettings.json`).
    *   Fetch usage examples from dependent services.
3.  **Report**:
    *   List potentially broken services.
    *   Highlight necessary updates in consumers.

### 3.3 Suggest Changes
1.  **Trigger**: "Refactor Service A to use the new Auth API".
2.  **Execution**:
    *   Agent identifies all call sites.
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

## 5. Security & Principles
*   **Least Privilege**: Only request necessary scopes for GitLab/Mongo.
*   **Data Privacy**: Sensitive code is only sent to the configured LLM provider.
*   **Audit**: All agent actions are logged.
