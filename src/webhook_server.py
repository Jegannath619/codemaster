from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import os
import json
from typing import Dict, Any
from src.agent import CodeMasterAgent
from src.llm.openai_client import OpenAIProvider

app = FastAPI(title="Code Master Webhook Server")

# Initialize Agent (Single instance for now)
llm = OpenAIProvider()
agent = CodeMasterAgent(llm)

@app.on_event("startup")
async def startup_event():
    await agent.initialize()

@app.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint to receive GitLab Webhooks.
    """
    # 1. Verify Token (Security)
    secret_token = request.headers.get("X-Gitlab-Token")
    expected_token = os.getenv("WEBHOOK_SECRET", "dummy_secret")
    if secret_token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid Token")

    payload = await request.json()
    event_type = payload.get("object_kind")

    print(f"[Webhook] Received event: {event_type}")

    if event_type == "push":
        # Handle Push Event -> Incremental Indexing
        background_tasks.add_task(process_push_event, payload)
        return {"status": "processing", "message": "Push event queued for indexing"}

    elif event_type == "merge_request":
        # Handle Merge Request -> Trigger Review (Optional, or explicit trigger)
        # We might only want to review on 'open' or 'update' actions
        action = payload.get("object_attributes", {}).get("action")
        if action in ["open", "reopen", "update"]:
             background_tasks.add_task(process_mr_event, payload)
             return {"status": "processing", "message": "Merge Request queued for review"}

    return {"status": "ignored", "message": f"Event {event_type} ignored"}

async def process_push_event(payload: Dict[str, Any]):
    """
    Extracts changed files and triggers incremental indexing.
    """
    project_id = str(payload.get("project_id"))
    commits = payload.get("commits", [])

    # 1. Identify modified files
    modified_files = {}
    for commit in commits:
        # GitLab push payload usually contains lists of added/modified/removed files
        # We need actual content, but the payload only gives paths.
        # So we must fetch content from GitLab API via the Agent.
        paths = commit.get("added", []) + commit.get("modified", [])
        for path in paths:
            # Heuristic: Determine service name from path (e.g., src/ServiceA/...)
            service_name = _extract_service_name(path)
            if service_name != "UnknownService":
                # Fetch content
                content = await agent.gitlab.get_file_content(project_id, path, ref=payload.get("checkout_sha"))
                if service_name not in modified_files:
                    modified_files[service_name] = {}
                modified_files[service_name][path] = content

    # 2. Trigger Incremental Indexing per service
    for service_name, files in modified_files.items():
        print(f"[Webhook] Triggering incremental index for {service_name} ({len(files)} files)")
        await agent.rag_indexer.ingest_changes(project_id, service_name, files)

async def process_mr_event(payload: Dict[str, Any]):
    """
    Triggers Code Review for a Merge Request.
    """
    project = payload.get("project", {})
    project_id = str(project.get("id"))
    mr_attr = payload.get("object_attributes", {})
    mr_iid = mr_attr.get("iid")

    if project_id and mr_iid:
        print(f"[Webhook] Triggering Code Review for MR {mr_iid}")
        await agent.run_code_review(project_id, mr_iid)

def _extract_service_name(filepath: str) -> str:
    # Reusing the simple heuristic from DependencyGraphBuilder
    parts = filepath.split('/')
    if len(parts) > 1 and parts[0] == "src":
        return parts[1]
    return "UnknownService"
