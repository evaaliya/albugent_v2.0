import os
import sys
import json
from dotenv import load_dotenv
from pathlib import Path
from collections import defaultdict

# Выравниваем пути
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strands import Agent
from strands.models import BedrockModel

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from mcp_server.mcp_server import scan_enterprise_datasets
from context_builder.context_builder import collect_governance_context
from mcp_server.utils.github_utils import create_remediation_pr
from mcp_server.utils.remediation_generator import generate_remediation_sql
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
# Импортируем системный промпт
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
    max_tokens=8000,
)


def build_sql_remediation_artifact(context_data: dict) -> str:
    datasets = context_data.get("datasets", [])
    if not datasets:
        return "-- No datasets found for remediation.\nSELECT 1;"

    sql_scripts = []
    for ds in datasets:
        table_name = ds.get("table_name", "unknown_table")
        profile_data = ds.get("statistical_profile", {})
        pii_columns = ds.get("pii_columns", [])  # ← добавили
        table_sql = generate_remediation_sql(table_name, profile_data, pii_columns)  # ← передали
        sql_scripts.append(table_sql)

    return "\n\n".join(sql_scripts)


def summarize_anomalies_for_prompt(raw_context: dict) -> str:
    """Разворачивает вложенный statistical_profile каждого датасета в плоский текстовый отчёт."""
    datasets = raw_context.get("datasets", [])
    report_lines = []

    for ds in datasets:
        urn = ds.get("urn", "unknown_dataset")
        profile = ds.get("statistical_profile", {})
        pii_columns = ds.get("pii_columns", [])   # ← добавить эту строку

        rows = []
        for item in profile.get("null_anomalies", []):
            rows.append(f"  - Column '{item['column']}': {item['null_count']} NULL values ({item['null_percentage']}%)")
        for item in profile.get("high_null_rate_columns", []): 
            rows.append(f"  - Column '{item['column']}': {item['null_count']} NULLs ({item['null_percentage']}%)")
        for item in profile.get("numeric_anomalies", []):
            if "issue" in item:
                rows.append(f"  - Column '{item['column']}': {item['invalid_count']} invalid_age_range ({item['percentage']}%)")
            else:
                rows.append(f"  - Column '{item['column']}': {item['negative_count']} negative values ({item['negative_percentage']}%)")
        for item in profile.get("date_logic_anomalies", []):
            rows.append(f"  - Columns '{item['col_1']}'/'{item['col_2']}': {item['inverted_rows_count']} inverted date rows ({item['percentage']}%)")
        for col in pii_columns:                    # ← добавить этот блок
            rows.append(f"  - Column '{col}': PII detected (sensitive data)")

        if rows:
            report_lines.append(f"Dataset: {urn}")
            report_lines.extend(rows)

    return "\n".join(report_lines) if report_lines else "No anomalies detected across registered datasets."

mcp_tools_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="python",
        args=["-m", "mcp_server.mcp_server"],
        cwd="/app"   # или откуда у тебя запускается agent.py внутри контейнера — проверь через WORKDIR в dockerfile
    )
))

ALLOWED_INVESTIGATION_TOOLS = {
    "list_available_datasets",
    "inspect_dataset_schema",
    "auto_profile_dataset_anomalies",
    "score_dataset_risk",
}

def filter_tools(all_tools, allowed_names):
    return [t for t in all_tools if t.tool_name in allowed_names]

def main():
    console.print(Panel.fit(
        "[bold white]🤖 ALBUGENT 2.0: AUTONOMOUS DATA GOVERNANCE ENGINE[/bold white]\n"
        "[dim]Powered by AWS Strands SDK & Bedrock Nova Pro (CI/CD Mode)[/dim]",
        style="blue"
    ))

    # 1. ДЕТЕРМИНИРОВАННЫЙ СБОР КОНТЕКСТА
    with console.status("[bold cyan]Gathering Deterministic Governance Context...", spinner="dots"):
        dataset_registry = scan_enterprise_datasets()   # свежий скан вместо статического импорта
        raw_context = collect_governance_context(dataset_registry)
    
    console.print("[info]✅ Governance Context fully aggregated.[/info]")

    # 2. РАЗДЕЛЬНАЯ ГЕНЕРАЦИЯ АРТЕФАКТОВ
    # А. Чистый SQL-код без участия LLM
    console.print("\n[bold green]🛠️ Building Deterministic SQL Remediation Artifact...[/bold green]")
    sql_code = build_sql_remediation_artifact(raw_context)

    # Б. Agentic-расследование + отчёт через LLM с доступом к investigation tools
    with console.status("[bold cyan]Agent investigating datasets...", spinner="dots"):
        with mcp_tools_client:
            all_tools = mcp_tools_client.list_tools_sync()
            limited_tools = filter_tools(all_tools, ALLOWED_INVESTIGATION_TOOLS)

            agent = Agent(
                model=bedrock_model,
                system_prompt=GOVERNANCE_SYSTEM_PROMPT,
                tools=limited_tools
          )

            pr_body_raw = str(agent(
                "Investigate every registered dataset using your available tools: call "
                "list_available_datasets first, then for each dataset call inspect_dataset_schema, "
                "auto_profile_dataset_anomalies, and score_dataset_risk. "
                "Do NOT write any report text between datasets — only call tools and silently "
                "accumulate findings until every dataset has been investigated. "
                "Only after you have investigated ALL datasets, compose exactly ONE final "
                "consolidated governance PR report covering every dataset in a single Table of "
                "Quality Variances, following your system instructions."
            )).strip()

    pr_body = pr_body_raw
    if "```markdown" in pr_body:
        pr_body = pr_body.split("```markdown")[1].split("```")[0].strip()
    elif "```" in pr_body:
        pr_body = pr_body.split("```")[1].split("```")[0].strip()

    pr_body = pr_body.replace("\\n", "\n")
    console.print("\n[bold green]✅ Governance Artifacts Successfully Constructed![/bold green]")

    # 3. СБОРКА И ОТПРАВКА ЕДИНОГО DRAFT PR В GITHUB
    repo_name = os.getenv("GITHUB_REPOSITORY", "evaaliya/albugent_v2.0")
    
    console.print("\n[bold yellow]🚀 Dispatching Unified Draft Remediation PR to GitHub...[/bold yellow]")
    
    with console.status("[bold green]Creating Draft Pull Request...", spinner="earth"):
        pr_url = create_remediation_pr(
            repo_name=repo_name,
            pr_title="🚨 [Albugent Draft] Automated Data Cleansing & Circuit Breaker Proposal",
            pr_body_markdown=pr_body,                  # Текст отчета от LLM
            remediation_file_path="models/cleaned_patients.sql",
            remediation_sql_code=sql_code              # Детерминированный SQL-код
        )

    if "http" in pr_url:
        console.print(f"\n[bold green]✅ Unified Draft PR successfully created for Review:[/bold green]")
        console.print(f"[bold highlight]{pr_url}[/bold highlight]\n")
    else:
        console.print(f"\n[bold red]❌ Failed to create PR: {pr_url}[/bold red]\n")

if __name__ == "__main__":
    main()