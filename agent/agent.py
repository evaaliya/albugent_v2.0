import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from strands import Agent, tool
from strands.models import BedrockModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from github import Github

from prompts.system_prompts import SYSTEM_PROMPT


class GitHubEngine:
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.repo_name = os.environ.get("GITHUB_REPOSITORY")
        self.gh = Github(self.token) if (self.token and self.repo_name) else None

    def create_remediation_pr(self, artifacts: Dict[str, str], summary_md: str) -> str:
        if not self.gh:
            print("[Git Engine] Run mode: Local dry-run (GITHUB_TOKEN missing).")
            return "Local execution complete."

        try:
            repo = self.gh.get_repo(self.repo_name)
            default_branch = repo.default_branch
            ref = repo.get_git_ref(f"heads/{default_branch}")
            
            branch_name = f"fix/albugent-governance-{int(datetime.now().timestamp())}"
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=ref.object.sha)

            for filepath, content in artifacts.items():
                if not content:
                    continue
                repo.create_file(
                    path=f"generated_code/{filepath}",
                    message=f"Albugent 2.0: Auto-remediation for {filepath}",
                    content=content,
                    branch=branch_name
                )

            pr = repo.create_pull(
                title="🤖 [Albugent 2.0] Automated Lineage & PII Remediation PR",
                body=summary_md,
                head=branch_name,
                base=default_branch
            )
            print(f"🚀 [SUCCESS] Created GitHub PR: {pr.html_url}")
            return pr.html_url
        except Exception as e:
            print(f"[Git Engine Error] {e}")
            return str(e)


async def run_albugent_pipeline():
    print("==========================================================")
    print("   LAUNCHING ALBUGENT 2.0 (Strands SDK + AWS Bedrock)    ")
    print("==========================================================")

    mcp_params = StdioServerParameters(
        command="python",
        args=["/app/mcp_server/mcp_server.py"],
        env=os.environ.copy()
    )

    bedrock_model = BedrockModel(
        model_id=os.environ.get("AWS_BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0"),
        region_name=os.environ.get("AWS_REGION", "us-east-1")
    )

    async with stdio_client(mcp_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Получаем текущий активный event loop
            loop = asyncio.get_running_loop()

            @tool
            def analyze_lineage_graph(nodes: List[str], edges: List[List[str]]) -> str:
                """Analyzes lineage graph for dataset nodes and edges to calculate centrality scores."""
                coro = session.call_tool("analyze_lineage_graph", {"nodes": nodes, "edges": edges})
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                res = future.result(timeout=30)
                return str(res.content)

            @tool
            def score_dataset_risk(
                urn: str,
                fields: List[str],
                centrality: float,
                is_orphan: bool,
                last_updated_ts: float = 0.0
            ) -> str:
                """Calculates total governance risk score for a dataset based on PII fields and centrality."""
                payload = {
                    "urn": urn,
                    "fields": fields,
                    "centrality": centrality,
                    "is_orphan": is_orphan,
                    "last_updated_ts": last_updated_ts
                }
                coro = session.call_tool("score_dataset_risk", payload)
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                res = future.result(timeout=30)
                return str(res.content)

            tools_for_agent = [analyze_lineage_graph, score_dataset_risk]

            agent = Agent(
                model=bedrock_model,
                system_prompt=SYSTEM_PROMPT,
                tools=tools_for_agent
            )

            mock_nodes = [
                "urn:li:dataset:(postgres,healthcare_billing,PROD)",
                "urn:li:dataset:(hive,nyc_taxi_trips,PROD)",
                "urn:li:dataset:(snowflake,retail_customer_analytics,PROD)"
            ]
            mock_edges = [
                ["urn:li:dataset:(postgres,healthcare_billing,PROD)", "urn:li:dataset:(snowflake,retail_customer_analytics,PROD)"]
            ]

            print("\n[Agent Loop] Executing background audit and risk analysis...")

            prompt_task = f"""
            Perform governance audit for dataset nodes: {json.dumps(mock_nodes)} 
            and lineage edges: {json.dumps(mock_edges)}.
            Use the 'analyze_lineage_graph' tool to calculate centrality, and 'score_dataset_risk' 
            for table fields ['id', 'patient_name', 'ssn', 'billing_amount'].
            """

            # Вызываем агента асинхронно через run_in_executor или напрямую, так как тулы теперь потокобезопасны
            response = await asyncio.to_thread(agent, prompt_task)

            print(f"\n[Strands Agent Decision Output]:\n{response}")


if __name__ == "__main__":
    asyncio.run(run_albugent_pipeline())