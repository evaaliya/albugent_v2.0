import os
import sys
import json
from dotenv import load_dotenv
from pathlib import Path

# Выравниваем пути
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strands import Agent
from strands.models import BedrockModel

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from mcp_server.mcp_server import DATASET_REGISTRY
from context_builder.context_builder import collect_governance_context
from mcp_server.utils.github_utils import create_remediation_pr

# Импортируем системный промпт из твоего файла system_prompts.py
from prompts.system_prompts import GOVERNANCE_SYSTEM_PROMPT

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


def main():
    console.print(Panel.fit(
        "[bold white]🤖 ALBUGENT 2.0: AUTONOMOUS DATA GOVERNANCE ENGINE[/bold white]\n"
        "[dim]Powered by AWS Strands SDK & Bedrock Nova Pro (CI/CD Mode)[/dim]",
        style="blue"
    ))

    # 1. ДЕТЕРМИНИРОВАННЫЙ СБОР ДАННЫХ
    with console.status("[bold cyan]Gathering Deterministic Governance Context...", spinner="dots"):
        raw_context = collect_governance_context(DATASET_REGISTRY)
        context_json_str = json.dumps(raw_context, indent=2, ensure_ascii=False)
    
    console.print("[info]✅ Governance Context (Profile, Lineage, Risk) fully aggregated.[/info]")

    # 2. ИНИЦИАЛИЗАЦИЯ И ВЫЗОВ АГЕНТА
    agent = Agent(
        model=bedrock_model,
        system_prompt=GOVERNANCE_SYSTEM_PROMPT
    )

    user_payload_message = (
        "Run a full governance audit on the following pre-computed enterprise pipeline payload:\n\n"
        f"```json\n{context_json_str}\n```"
    )

    with console.status("[bold green]Executing Cognitive Governance Audit...", spinner="dots"):
        audit_response = agent(user_payload_message)

     # Жесткое извлечение JSON из ответа
    raw_response = str(audit_response).strip()
    
    # Режем всё, что выходит за пределы фигурных скобок JSON
    if "{" in raw_response and "}" in raw_response:
        start_idx = raw_response.find("{")
        end_idx = raw_response.rfind("}") + 1
        raw_response = raw_response[start_idx:end_idx]

    try:
        data = json.loads(raw_response)
        pr_body = data.get("pr_body", "Error parsing PR body markdown.")
        remediation_path = data.get("remediation_file_path", "models/cleaned_patients.sql")
        sql_code = data.get("sql_code", "-- No SQL code generated")
    except Exception as e:
        console.print(f"[bold red]⚠️ Failed to parse JSON: {e}[/bold red]")
        pr_body = f"## 🛡️ Data Governance Audit Report\n\n{str(audit_response)}"
        remediation_path = "models/cleaned_patients.sql"
        sql_code = "-- Error parsing model response"

    console.print("\n[bold green]✅ Audit response successfully processed.[/bold green]")
    console.print(Panel(
        f"[bold font]{pr_body}[/bold font]",
        title="[bold cyan]Generated Audit Summary[/bold cyan]",
        border_style="cyan"
    ))

    # 3. АВТОНОМНОЕ СОЗДАНИЕ DRAFT PR (HITL via GitHub UI)
    repo_name = os.getenv("GITHUB_REPOSITORY", "evaaliya/albugent_v2.0")
    
    console.print("\n[bold yellow]🚀 Dispatching Automated Draft Remediation PR to GitHub...[/bold yellow]")
    
    with console.status("[bold green]Creating Draft Pull Request...", spinner="earth"):
        pr_url = create_remediation_pr(
            repo_name=repo_name,
            pr_title="🚨 [Albugent Draft] Automated Data Cleansing & Circuit Breaker Proposal",
            pr_body_markdown=pr_body,
            remediation_file_path=remediation_path,
            remediation_sql_code=sql_code
        )

    if "http" in pr_url:
        console.print(f"\n[bold green]✅ Draft PR successfully created for Human Review:[/bold green]")
        console.print(f"[bold highlight]{pr_url}[/bold highlight]\n")
    else:
        console.print(f"\n[bold red]❌ Failed to create PR: {pr_url}[/bold red]\n")


if __name__ == "__main__":
    main()