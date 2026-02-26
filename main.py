import asyncio
import argparse
from src.agents.orchestrator import Orchestrator
from src.llm.openai_client import OpenAIProvider

async def main():
    parser = argparse.ArgumentParser(description="Agentic SDLC Co-pilot CLI")
    parser.add_argument("--action", choices=["review", "impact", "chat"], required=True, help="Action to perform")
    parser.add_argument("--project-id", type=str, help="GitLab Project ID")
    parser.add_argument("--mr-iid", type=int, help="Merge Request IID")
    parser.add_argument("--service-name", type=str, help="Service Name")
    parser.add_argument("--query", type=str, help="Chat query")

    args = parser.parse_args()

    llm = OpenAIProvider()
    orchestrator = Orchestrator(llm)
    await orchestrator.initialize()

    if args.action == "review":
        if not args.mr_iid or not args.project_id:
            print("Error: --mr-iid and --project-id required for review.")
            return
        result = await orchestrator.run_review(args.project_id, args.mr_iid)
        print("\n--- Review Result ---\n")
        print(result)

    elif args.action == "impact":
        if not args.service_name or not args.project_id:
            print("Error: --service-name and --project-id required for impact analysis.")
            return
        result = await orchestrator.run_impact(args.project_id, args.service_name)
        print("\n--- Impact Analysis ---\n")
        print(result)

    elif args.action == "chat":
        if not args.query:
            print("Error: --query required for chat.")
            return
        result = await orchestrator.run_chat(args.query)
        print("\n--- Answer ---\n")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
