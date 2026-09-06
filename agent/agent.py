import os
import sys
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

from mcp_server.mcp_server import scan_enterprise_datasets
from context_builder.context_builder import collect_governance_context
from mcp_server.utils.github_utils import create_remediation_pr
from mcp_server.utils.remediation_generator import generate_remediation_sql

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
    """
    Собирает SQL-артефакты ремедиации для всех датасетов из контекста,
    используя детерминированный генератор. Без участия LLM.
    """
    datasets = context_data.get("datasets", [])

    if not datasets:
        return "-- No datasets found for remediation.\nSELECT 1;"

    sql_scripts = []

    for ds in datasets:
        table_name = ds.get("table_name", "unknown_table")
        profile_data = ds.get("statistical_profile", {})
        pii_columns = ds.get("pii_columns", [])

        table_sql = generate_remediation_sql(table_name, profile_data, pii_columns)
        sql_scripts.append(table_sql)

    return "\n\n".join(sql_scripts)


def build_quality_variances_table(raw_context: dict) -> str:
    """
    Строит Table of Quality Variances детерминированно в Python.
    Агрегирует одинаковые находки (та же колонка + тип ошибки + row count)
    across pipeline-стадий в одну строку — без участия LLM, значит без
    риска непоследовательной агрегации.
    """
    lines = [
        "### Table of Quality Variances",
        "",
        "| Dataset URN | Column | Error Type | Row Count | Status |",
        "| --- | --- | --- | --- | --- |",
    ]

    seen: dict = {}  # (column, error_type, row_count) -> [urns]

    for ds in raw_context.get("datasets", []):
        urn = ds["urn"]
        profile = ds.get("statistical_profile", {})

        for item in profile.get("null_anomalies", []):
            key = (item["column"], "NULL values", item["null_count"])
            seen.setdefault(key, []).append(urn)

        for item in profile.get("high_null_rate_columns", []):
            key = (item["column"], "High NULL Rate (Likely By-Design)", item["null_count"])
            seen.setdefault(key, []).append(urn)

        for item in profile.get("numeric_anomalies", []):
            if "issue" in item:
                key = (item["column"], "Invalid age range", item["invalid_count"])
            else:
                key = (item["column"], "Negative values", item["negative_count"])
            seen.setdefault(key, []).append(urn)

        for item in profile.get("date_logic_anomalies", []):
            col_pair = f"{item['col_1']}, {item['col_2']}"
            key = (col_pair, "Date logic inversion", item["inverted_rows_count"])
            seen.setdefault(key, []).append(urn)

    for (column, error_type, count), urns in seen.items():
        urn_list = ", ".join(f"`{u}`" for u in urns)
        status = "Informational" if "By-Design" in error_type else "Pending Review"
        lines.append(f"| {urn_list} | {column} | {error_type} | {count} | {status} |")

    if not seen:
        lines.append("| — | — | No anomalies detected | — | — |")

    return "\n".join(lines)


def build_pii_section(raw_context: dict) -> str:
    """Строит PII Detections таблицу детерминированно. Без участия LLM."""
    pii_datasets = [ds for ds in raw_context.get("datasets", []) if ds.get("pii_columns")]

    if not pii_datasets:
        return "### PII Detections\n\nNo PII columns detected across registered datasets."

    lines = ["### PII Detections", "", "| Dataset URN | PII Columns |", "| --- | --- |"]
    for ds in pii_datasets:
        cols = ", ".join(ds["pii_columns"])
        lines.append(f"| `{ds['urn']}` | {cols} |")

    return "\n".join(lines)


def build_circuit_breaker_section(raw_context: dict) -> str:
    """Строит Circuit Breaker Status таблицу детерминированно. Без участия LLM."""
    lines = [
        "### Pipeline Lineage & Circuit Breaker Status",
        "",
        "| Dataset URN | Circuit Breaker Status |",
        "| --- | --- |",
    ]
    for ds in raw_context.get("datasets", []):
        status = ds.get("circuit_breaker_status", "OK")
        lines.append(f"| `{ds['urn']}` | {status} |")

    return "\n".join(lines)


def generate_executive_summary(raw_context: dict) -> str:
    """
    ЕДИНСТВЕННЫЙ LLM-вызов во всём пайплайне. Не оркестрация, не tool-use —
    просто написать несколько предложений поверх уже вычисленных фактов.
    Модель не может галлюцинировать данные, которых нет в промпте, потому что
    у неё нет доступа ни к каким tools для "самостоятельного расследования".
    """
    datasets = raw_context.get("datasets", [])
    total_datasets = len(datasets)

    halted = [ds["urn"] for ds in datasets if ds.get("circuit_breaker_status") == "HALTED"]

    total_anomalies = 0
    pii_dataset_count = 0
    for ds in datasets:
        profile = ds.get("statistical_profile", {})
        total_anomalies += (
            len(profile.get("null_anomalies", []))
            + len(profile.get("numeric_anomalies", []))
            + len(profile.get("date_logic_anomalies", []))
        )
        if ds.get("pii_columns"):
            pii_dataset_count += 1

    prompt = (
        "Write a concise, professional Executive Summary (3-4 sentences) for a data governance "
        "audit PR report, based ONLY on the following verified facts. Do not invent, estimate, or "
        "add any numbers or dataset names beyond what is given here.\n\n"
        f"- Total datasets investigated: {total_datasets}\n"
        f"- Total quality anomalies found: {total_anomalies}\n"
        f"- Datasets flagged with PII: {pii_dataset_count}\n"
        f"- Datasets currently halted by the circuit breaker: {len(halted)}\n\n"
        "Output ONLY the summary paragraph. No headers, no bullet points, no commentary."
    )

    agent = Agent(
        model=bedrock_model,
        system_prompt="You are a concise technical writer producing enterprise data governance reports."
    )
    return str(agent(prompt)).strip()


def main():
    console.print(Panel.fit(
        "[bold white]🤖 ALBUGENT 2.0: AUTONOMOUS DATA GOVERNANCE ENGINE[/bold white]\n"
        "[dim]Powered by AWS Strands SDK & Bedrock Nova Pro (CI/CD Mode)[/dim]",
        style="blue"
    ))

    with console.status("[bold cyan]Gathering Deterministic Governance Context...", spinner="dots"):
        dataset_registry = scan_enterprise_datasets()
        raw_context = collect_governance_context(dataset_registry)

    console.print("[info]✅ Governance Context fully aggregated.[/info]")

    console.print("\n[bold green]🛠 Building Deterministic SQL Remediation Artifact...[/bold green]")
    sql_code = build_sql_remediation_artifact(raw_context)

    console.print("\n[bold green]📋 Building Deterministic Report Sections...[/bold green]")
    quality_table = build_quality_variances_table(raw_context)
    pii_section = build_pii_section(raw_context)
    circuit_breaker_section = build_circuit_breaker_section(raw_context)

    with console.status("[bold cyan]Generating Executive Summary via Bedrock...", spinner="dots"):
        executive_summary = generate_executive_summary(raw_context)

    pr_body = (
        f"## Data Governance and Quality Engineering Report\n\n"
        f"### Executive Summary\n\n{executive_summary}\n\n"
        f"{quality_table}\n\n"
        f"{pii_section}\n\n"
        f"{circuit_breaker_section}\n\n"
        f"### Deterministic Remediation Strategy\n\n"
        f"The proposed remediation uses safe `CASE WHEN` and `COALESCE` SQL patterns to address "
        f"data quality issues. PII columns are flagged for governance review and are never "
        f"automatically modified by the SQL script."
    )

    console.print("\n[bold green]✅ Governance Artifacts Successfully Constructed![/bold green]")

    repo_name = os.getenv("GITHUB_REPOSITORY", "evaaliya/albugent_v2.0")

    console.print("\n[bold yellow]🚀 Dispatching Unified Draft Remediation PR to GitHub...[/bold yellow]")

    with console.status("[bold green]Creating Draft Pull Request...", spinner="earth"):
        pr_url = create_remediation_pr(
            repo_name=repo_name,
            pr_title="🚨 [Albugent Draft] Automated Data Cleansing & Circuit Breaker Proposal",
            pr_body_markdown=pr_body,
            remediation_file_path="models/cleaned_patients.sql",
            remediation_sql_code=sql_code
        )

    if "http" in pr_url:
        console.print(f"\n[bold green]✅ Unified Draft PR successfully created for Review:[/bold green]")
        console.print(f"[bold highlight]{pr_url}[/bold highlight]\n")
        return {"status": "success", "pr_url": pr_url}
    else:
        console.print(f"\n[bold red]❌ Failed to create PR: {pr_url}[/bold red]\n")
        return {"status": "error", "message": pr_url}


if __name__ == "__main__":
    main()