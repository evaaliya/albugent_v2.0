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

    # =========================================================================
    # 2. ИНИЦИАЛИЗАЦИЯ И ДВУХШАГОВАЯ ГЕНЕРАЦИЯ (Без JSON-парсинга и блокировок)
    # =========================================================================
    agent = Agent(
        model=bedrock_model,
        system_prompt=GOVERNANCE_SYSTEM_PROMPT
    )

    # --- ШАГ 1: Генерируем чистый SQL-код очистки данных ---
    sql_prompt = (
        "Analyze this data governance context and output ONLY valid ANSI SQL code "
        "to cleanse detected anomalies (NULLs, negative values, outliers). "
        "Do not write conversational text:\n\n"
        f"{context_json_str}"
    )
    
    with console.status("[bold green]Step 1/2: Generating SQL Remediation Script...", spinner="dots"):
        sql_response_raw = str(agent(sql_prompt)).strip()
        
    # Извлекаем чистый SQL из возможного markdown-блока ```sql
    if "```sql" in sql_response_raw:
        sql_code = sql_response_raw.split("```sql")[1].split("```")[0].strip()
    elif "```" in sql_response_raw:
        sql_code = sql_response_raw.split("```")[1].split("```")[0].strip()
    else:
        sql_code = sql_response_raw


    # --- ШАГ 2: Генерируем Markdown-отчет для PR Body ---
    pr_body_prompt = (
        "Generate a clean, professional GitHub Pull Request Markdown report "
        "based on this data audit payload. Include a Table of Quality Variances, "
        "Lineage Status (PAUSED / OPERATIONAL), and a note about staged SQL fixes. "
        "Do not wrap in JSON:\n\n"
        f"{context_json_str}"
    )

    with console.status("[bold cyan]Step 2/2: Generating PR Audit Summary...", spinner="dots"):
        pr_body_raw = str(agent(pr_body_prompt)).strip()

    # Извлекаем Markdown (если модель обернула его в ```markdown)
    if "```markdown" in pr_body_raw:
        pr_body = pr_body_raw.split("```markdown")[1].split("```")[0].strip()
    elif "```" in pr_body_raw and not pr_body_raw.startswith("##"):
        pr_body = pr_body_raw.split("```")[1].split("```")[0].strip()
    else:
        pr_body = pr_body_raw


    # --- ШАГ 3: Собираем безопасный Payload ---
    remediation_path = "models/cleaned_patients.sql"

    data_payload = {
        "pr_body": pr_body,
        "remediation_file_path": remediation_path,
        "sql_code": sql_code
    }

    console.print("\n[bold green]✅ Governance Artifacts Successfully Constructed![/bold green]")
    console.print(Panel(
        f"[bold font]{data_payload['pr_body']}[/bold font]",
        title="[bold cyan]Generated Audit Summary[/bold cyan]",
        border_style="cyan"
    ))


    # =========================================================================
    # 3. АВТОНОМНОЕ СОЗДАНИЕ DRAFT PR В GITHUB
    # =========================================================================
    repo_name = os.getenv("GITHUB_REPOSITORY", "evaaliya/albugent_v2.0")
    
    console.print("\n[bold yellow]🚀 Dispatching Automated Draft Remediation PR to GitHub...[/bold yellow]")
    
    with console.status("[bold green]Creating Draft Pull Request...", spinner="earth"):
        pr_url = create_remediation_pr(
            repo_name=repo_name,
            pr_title="🚨 [Albugent Draft] Automated Data Cleansing & Circuit Breaker Proposal",
            pr_body_markdown=data_payload["pr_body"],
            remediation_file_path=data_payload["remediation_file_path"],
            remediation_sql_code=data_payload["sql_code"]
        )

    if "http" in pr_url:
        console.print(f"\n[bold green]✅ Draft PR successfully created for Human Review:[/bold green]")
        console.print(f"[bold highlight]{pr_url}[/bold highlight]\n")
    else:
        console.print(f"\n[bold red]❌ Failed to create PR: {pr_url}[/bold red]\n")


if __name__ == "__main__":
    main()