import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv

from github import Github, GithubException, Auth

# MCP & Strands SDK Imports
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
from strands.models import BedrockModel

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

# Load Environment Variables
load_dotenv()

# Initialize Rich Console
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "magenta",
})
console = Console(theme=custom_theme)

# Initialize AWS Bedrock Model via Strands SDK
bedrock_model = BedrockModel(
    model_id=os.getenv("AWS_BEDROCK_MODEL_ID", "amazon.nova-pro-v1:0"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)

# -------------------------------------------------------------------
# 1. MCP Transport Factory Setup (AWS Strands Official Pattern)
# -------------------------------------------------------------------


mcp_server_path = "/app/mcp_server/mcp_server.py"
mcp_working_dir = "/app/mcp_server"

server_params = StdioServerParameters(
    command="python",
    args=[mcp_server_path],
    cwd=mcp_working_dir,  # Указываем подпроцессу запуск ИЗ папки mcp_server
    env=os.environ.copy()
)

def create_stdio_transport():
    """Factory function returning the Stdio client transport context."""
    return stdio_client(server_params)

# Initialize MCPClient with the factory
mcp_client = MCPClient(create_stdio_transport)


# -------------------------------------------------------------------
# 2. Tool: GitHub Auto-Remediation PR Tool
# -------------------------------------------------------------------
def create_remediation_pr(issue_description: str) -> str:
    """Generates an automated remediation branch and Pull Request on GitHub."""
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo_name = os.getenv("GITHUB_REPOSITORY")

    if not github_token or not github_repo_name:
        return "Error: GITHUB_TOKEN or GITHUB_REPOSITORY environment variables are missing."

    try:
        gh = Github(auth=Auth.Token(github_token))
        repo = gh.get_repo(github_repo_name)

        main_branch = repo.get_branch("main")
        new_branch_name = f"fix/albugent-governance-{os.urandom(4).hex()}"
        repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=main_branch.commit.sha)

        file_path = "remediation_report.md"
        content = (
            f"# 🛡️ Albugent Autonomous Remediation Report\n\n"
            f"**Audit Status:** Action Required\n"
            f"**Details:** {issue_description}\n\n"
            f"_Automated Governance Action Authorized by Human Operator._\n"
        )

        try:
            existing_file = repo.get_contents(file_path, ref=new_branch_name)
            repo.update_file(
                path=file_path,
                message="Albugent 2.0: Update governance remediation report",
                content=content,
                sha=existing_file.sha,
                branch=new_branch_name
            )
        except GithubException:
            repo.create_file(
                path=file_path,
                message="Albugent 2.0: Auto-remediation for remediation_report.md",
                content=content,
                branch=new_branch_name
            )

        pr = repo.create_pull(
            title="[Albugent 2.0] Automated Lineage & PII Remediation PR",
            body=(
                f"Automated governance remediation PR triggered by Albugent 2.0 Engine.\n\n"
                f"**Audit Summary:**\n{issue_description}"
            ),
            head=new_branch_name,
            base="main"
        )
        return f"SUCCESS: Created GitHub PR: {pr.html_url}"

    except Exception as e:
        return f"Error creating GitHub PR: {str(e)}"


# -------------------------------------------------------------------
# 3. Main Execution Workflow
# -------------------------------------------------------------------
def main():
    console.clear()
    console.print(Panel.fit(
        "[bold white]🤖 ALBUGENT 2.0: DATA GOVERNANCE ENGINE[/bold white]\n"
        "[dim]Powered by AWS Strands SDK, Native MCP, & Bedrock Nova Pro[/dim]",
        style="blue"
    ))

    # Connect to MCP server within Context Manager
    with mcp_client:
        console.print("[info]🔌 Connected to Custom MCP Server via Stdio Transport.[/info]")
        
        # Retrieve tools directly from the MCP Server
        mcp_tools = mcp_client.list_tools_sync()
        console.print(f"[info]🛠️ Loaded {len(mcp_tools)} MCP tools from server.[/info]")

        # Create Agent with combined tools (MCP + GitHub PR)
        agent = Agent(
            model=bedrock_model,
            tools=[*mcp_tools, create_remediation_pr],
            system_prompt=(
                "You are the Lead Data Governance Orchestrator for Albugent 2.0.\n"
                "Your workflow:\n"
                "1. Use `analyze_lineage_graph` and `score_dataset_risk` MCP tools to assess datasets.\n"
                "2. Evaluate dataset risks. If any dataset crosses the risk threshold of 0.65, "
                "highlight the vulnerability clearly.\n"
                "3. Provide a concise final decision summary."
            )
        )

        with console.status("[bold green]Executing Governance Audit...", spinner="dots"):
            audit_response = agent(
    "Run a full governance audit on the enterprise data pipeline. Identify high centrality nodes and PII risks."
)

    console.print("\n")
    console.print(Panel(
        f"[bold font]{audit_response}[/bold font]",
        title="[bold cyan]Final Agent Governance Decision[/bold cyan]",
        border_style="cyan"
    ))

    # Human-In-The-Loop (HITL) Guardrail
    console.print("\n")
    console.print(Panel(
        "[bold yellow]🚨 GOVERNANCE AUDIT COMPLETE[/bold yellow]\n"
        "High-priority or sensitive data lineage fields evaluated.\n"
        "Automated remediation is ready for deployment.",
        title="[bold red]Human-In-The-Loop Intervention Required[/bold red]",
        border_style="red"
    ))

    user_input = Prompt.ask(
        "\n[bold yellow]Do you authorize automated remediation and GitHub PR creation?[/bold yellow]",
        choices=["y", "n"],
        default="n"
    )

    if user_input.lower() == "y":
        console.print("\n[bold green]✅ Operator APPROVED remediation. Dispatching GitHub PR...[/bold green]")
        with console.status("[bold green]Creating pull request on GitHub...", spinner="earth"):
            pr_result = create_remediation_pr(str(audit_response))
        
        if "SUCCESS" in pr_result:
            console.print(f"\n[bold success]🚀 {pr_result}[/bold success]\n")
        else:
            console.print(f"\n[bold error]❌ {pr_result}[/bold error]\n")
    else:
        console.print("\n[bold red]🛑 Operator REJECTED remediation. Action cancelled.[/bold red]\n")

if __name__ == "__main__":
    main()