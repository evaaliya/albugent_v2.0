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

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
from rich.theme import Theme

from prompts.system_prompts import SYSTEM_PROMPT

# Настройка красивой консоли Rich
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green",
    "highlight": "magenta"
})
console = Console(theme=custom_theme)


# 1. GitHub Engine с поддержкой HITL
class GitHubEngine:
    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        self.repo_name = os.environ.get("GITHUB_REPOSITORY")
        self.gh = Github(self.token) if (self.token and self.repo_name) else None

    def create_remediation_pr(self, artifacts: Dict[str, str], summary_md: str) -> str:
        if not self.gh:
            console.print("[warning]⚠️ [Git Engine] Dry-run mode (GITHUB_TOKEN missing). Skipping PR creation.[/warning]")
            return "Dry-run execution complete."

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
            console.print(f"[success]🚀 Created GitHub PR:[/success] [link={pr.html_url}]{pr.html_url}[/link]")
            return pr.html_url
        except Exception as e:
            console.print(f"[danger]❌ [Git Engine Error]: {e}[/danger]")
            return str(e)


# 2. Основной оркестратор с HITL и Rich UI
async def run_albugent_pipeline():
    console.print(Panel.fit(
        "[bold magenta]ALBUGENT 2.0[/bold magenta] | Governance Agent Engine\n"
        "[dim]Powered by AWS Strands SDK + MCP + AWS Bedrock[/dim]",
        border_style="cyan"
    ))

    git_engine = GitHubEngine()

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
            with console.status("[bold info]Initializing MCP Analytics Session...", spinner="dots"):
                await session.initialize()

            loop = asyncio.get_running_loop()

            # --- Обертки инструментов MCP с красивым выводом ---
            @tool
            def analyze_lineage_graph(nodes: List[str], edges: List[List[str]]) -> str:
                """Analyzes lineage graph for dataset nodes and edges to calculate centrality scores."""
                console.print("[info]🔧 [MCP Tool] Executing analyze_lineage_graph...[/info]")
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
                console.print(f"[info]🔧 [MCP Tool] Scoring risk for {urn}...[/info]")
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
                
                # Разбор результата для HITL принятия решений
                try:
                    data = json.loads(res.content[0].text if isinstance(res.content, list) else res.content)
                    risk_score = data.get("risk_score", 0.0)
                    
                    # Визуализация результатов оценки в Rich Table
                    table = Table(title=f"Dataset Evaluation: {urn.split(',')[-2]}", show_header=True)
                    table.add_column("Property", style="cyan")
                    table.add_column("Value", style="bold white")
                    table.add_row("URN", urn)
                    table.add_row("Centrality", str(centrality))
                    
                    if risk_score >= 0.85:
                        table.add_row("Risk Score", f"[danger]{risk_score:.2f} (CRITICAL)[/danger]")
                    elif risk_score >= 0.65:
                        table.add_row("Risk Score", f"[warning]{risk_score:.2f} (MEDIUM)[/warning]")
                    else:
                        table.add_row("Risk Score", f"[success]{risk_score:.2f} (LOW)[/success]")
                    
                    console.print(table)

                    # --- Human-in-the-Loop (HITL) Логика ---
                    if risk_score >= 0.3: #<-- mock-test⚒️
                        console.print(Panel(
                            f"[danger]🚨 CRITICAL RISK DETECTED ({risk_score:.2f})[/danger]\n"
                            f"Dataset {urn} exceeds safety threshold (>= 0.85).",
                            title="Human-In-The-Loop Intervention Required",
                            border_style="red"
                        ))
                     
                    elif risk_score >= 0.65:
                        console.print(f"[warning]⚡ Medium risk detected ({risk_score:.2f}). Autonomously creating PR...[/warning]")
                        git_engine.create_remediation_pr(
                            artifacts={"remediation.md": f"# Auto Remediation for {urn}\nRisk: {risk_score}"},
                            summary_md=f"Automated remediation PR created for Medium Risk ({risk_score})."
                        )
                    else:
                        console.print(f"[dim]ℹ️ Low risk ({risk_score:.2f}). No remediation required.[/dim]")

                except Exception as e:
                    console.print(f"[warning]Failed to parse risk result for HITL: {e}[/warning]")

                return str(res.content)

            tools_for_agent = [analyze_lineage_graph, score_dataset_risk]

            agent = Agent(
                model=bedrock_model,
                system_prompt=SYSTEM_PROMPT,
                tools=tools_for_agent
            )

            # Мок-данные для проверки критического риска
            mock_nodes = [
                "urn:li:dataset:(postgres,healthcare_billing,PROD)",
                "urn:li:dataset:(hive,nyc_taxi_trips,PROD)",
                "urn:li:dataset:(snowflake,retail_customer_analytics,PROD)"
            ]
            mock_edges = [
                ["urn:li:dataset:(postgres,healthcare_billing,PROD)", "urn:li:dataset:(snowflake,retail_customer_analytics,PROD)"]
            ]

            console.print("\n[bold cyan]🤖 [Agent Loop] Starting Autonomous Governance Audit...[/bold cyan]")

            prompt_task = f"""
            Perform governance audit for dataset nodes: {json.dumps(mock_nodes)} 
            and lineage edges: {json.dumps(mock_edges)}.
            Use the 'analyze_lineage_graph' tool to calculate centrality, and 'score_dataset_risk' 
            for table fields ['id', 'patient_name', 'ssn', 'billing_amount'].
            """

            with console.status("[bold green]Agent thinking and executing tools...", spinner="bouncingBar"):
                response = await asyncio.to_thread(agent, prompt_task)

            console.print(Panel(
                str(response),
                title="[bold green]Final Agent Governance Decision[/bold green]",
                border_style="green"
            ))


if __name__ == "__main__":
    asyncio.run(run_albugent_pipeline())