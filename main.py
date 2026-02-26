import asyncio
import argparse
import os
from src.agent import CodeMasterAgent
from src.llm.openai_client import OpenAIProvider

async def main():
    parser = argparse.ArgumentParser(description="Agentic AI Code Master CLI")
    parser.add_argument("--action", choices=["review", "impact", "suggest"], required=True, help="Action to perform")
    parser.add_argument("--project-id", type=str, required=True, help="GitLab Project ID")
    parser.add_argument("--mr-iid", type=int, help="Merge Request IID (required for review)")
    parser.add_argument("--service-name", type=str, help="Service Name (required for impact)")
    parser.add_argument("--requirement", type=str, help="Requirement description (required for suggest)")
    parser.add_argument("--model", type=str, default="gpt-4o", help="LLM Model to use")

    args = parser.parse_args()

    # Initialize LLM Provider (swappable)
    llm = OpenAIProvider(model=args.model)

    # Initialize Agent
    agent = CodeMasterAgent(llm)
    await agent.initialize()

    if args.action == "review":
        if not args.mr_iid:
            print("Error: --mr-iid is required for review.")
            return
        result = await agent.run_code_review(args.project_id, args.mr_iid)
        print("\n--- Review Result ---\n")
        print(result)

    elif args.action == "impact":
        if not args.service_name:
            print("Error: --service-name is required for impact analysis.")
            return
        result = await agent.run_impact_analysis(args.project_id, args.service_name)
        print("\n--- Impact Analysis ---\n")
        print(result)

    elif args.action == "suggest":
        if not args.requirement:
            print("Error: --requirement is required for suggestions.")
            return
        result = await agent.suggest_changes(args.project_id, args.requirement)
        print("\n--- Code Suggestion ---\n")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
