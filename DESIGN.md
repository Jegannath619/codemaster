# Agentic SDLC Co-pilot - Design Document

## 1. Vision and Scope
The **Agentic SDLC Co-pilot** (formerly Code Master) is a multi-agent system designed to assist in the microservices lifecycle. It goes beyond simple linting or RAG to provide:
-   **Talk-to-code**: Conversational understanding of architecture and logic.
-   **Agentic Code Review**: Multi-phase review by specialized agents (Context, Intent, Risk).
-   **Impact Analysis**: Combining static code graphs (DKB) with runtime topology (Dynatrace).
-   **Quality Context**: Integrating SonarQube static analysis with runtime risk.

## 2. Architecture

```
+------------------+      +------------------+      +-------------------+
|  CLI / Webhook   | <--> |   Orchestrator   | <--> |   LLM Provider    |
|   (Interfaces)   |      | (src/agents/*)   |      | (src/llm/base.py) |
+------------------+      +--------+---------+      +-------------------+
                                   |
                                   v
                        +----------------------+
                        |   Analysis Engine    |
                        | (DKB Graph + RAG)    |
                        +----------+-----------+
                                   |
            +----------------------+----------------------+
            |                      |                      |
    +-------v-------+      +-------v-------+      +-------v-------+
    | GitLab Client |      | Sonar Client  |      | Dynatrace Client|
    | (src/gitlab/) |      | (src/sonar/)  |      | (src/dynatrace/)|
    +---------------+      +---------------+      +---------------+
```

### 2.1 Multi-Agent System (`src/agents/`)

Instead of a monolithic agent, we use specialized sub-agents orchestrated to mimic a senior engineer's workflow.

*   **Orchestrator**: Routes user intents (Review, Impact, Chat) to the right workflow.
*   **Reviewer Agent**:
    1.  **Context Mapper**: Identifies services, modules, and contracts touched by the MR.
    2.  **Intent Inference**: Extracts the "why" from MR description and tickets.
    3.  **Risk Hypothesis**: Generates targeted questions ("Does this break the Order API consumer?").
    4.  **Consolidator**: Merges findings into a coherent report.
*   **Impact Analyst Agent**:
    -   Uses **DKB (Deterministic Knowledge Graph)** for static dependencies (Controller -> Service -> Repo).
    -   Uses **Dynatrace Connector** for runtime topology (Service Flow, Traffic).
    -   Uses **SonarQube Connector** for existing technical debt.

### 2.2 Integration Layer

*   **GitLab**: Source code, MRs, Commits (via MCP/API).
*   **MongoDB**: Stores the Knowledge Graph (DKB), RAG Chunks, and Conversation History.
*   **SonarQube**: Static analysis metrics and issues (New).
*   **Dynatrace**: Runtime metrics, service topology, and SLOs (New).

### 2.3 RAG Pipeline (DKB-RAG)

*   **Indexing**: Incremental AST-based chunking (simulated Tree-sitter).
*   **Retrieval**: Hybrid search (Graph Traversal + Semantic + Keyword).

## 3. Workflows

### 3.1 Talk-to-Code
-   **User**: "How does the PaymentService interact with the OrderService?"
-   **System**: Retrieves the DKB graph nodes, fetches relevant code chunks, checks Dynatrace for runtime traffic, and synthesizes an answer.

### 3.2 Agentic Code Review
1.  **Trigger**: GitLab Webhook (MR Open/Update).
2.  **Context**: Fetch diffs, Sonar reports for changed files.
3.  **Analysis**:
    -   Run DKB analysis to find dependent components.
    -   LLM Agents review logic, security, and performance.
4.  **Output**: Summary comment on MR + specific actionable threads.

### 3.3 Runtime-Aware Impact Analysis
1.  **Trigger**: "What if I change the `ProcessOrder` signature?"
2.  **Static**: DKB finds `OrderController` calls `ProcessOrder`.
3.  **Runtime**: Dynatrace reveals `OrderController` is called by `MobileApp` (high traffic).
4.  **Report**: "High Risk. This change affects the MobileApp (10k req/min)."

## 4. Configuration
Configuration via `.env`:
*   `GITLAB_API_URL`, `GITLAB_TOKEN`
*   `SONAR_HOST_URL`, `SONAR_TOKEN`
*   `DYNATRACE_URL`, `DYNATRACE_TOKEN`
*   `MONGODB_URI`
*   `LLM_API_KEY`
