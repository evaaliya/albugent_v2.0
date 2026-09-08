from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from mcp_server.utils.db_utils import get_table_fields
from mcp_server.utils.lineage_discoverer import discover_lineage_edges
from mcp_server.utils.pii_detector import detect_pii_columns


from mcp_server.mcp_server import (
    DATASET_REGISTRY,
    score_all_datasets_risk,
    inspect_dataset_schema,
    get_remediation_patches,
)

app = FastAPI(title="Albugent Web API")

# На деве разрешаем фронт с любого порта; сузьте origin на проде
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/kpi-summary")
def kpi_summary() -> Dict[str, Any]:
    """Питает верхний KPI-баннер. PII считается напрямую через inspect_dataset_schema,
    не завязано на risk-scoring цепочку."""
    risk_data = score_all_datasets_risk()

    total_pii_columns = 0
    for urn in DATASET_REGISTRY.keys():
        schema = inspect_dataset_schema(urn)
        total_pii_columns += len(schema.get("detected_pii_fields", []))

    return {
        "data_assets": len(DATASET_REGISTRY),
        "tables_scanned": len(DATASET_REGISTRY),
        "pii_columns": total_pii_columns,
        "policy_violations": risk_data["summary"]["high_risk_count"],
    }

@app.get("/api/pii-distribution")
def pii_distribution() -> Dict[str, Any]:
    from mcp_server.utils.pii_detector import classify_pii_severity

    counts = {"High": 0, "Medium": 0, "Low": 0}
    for urn in DATASET_REGISTRY.keys():
        schema = inspect_dataset_schema(urn)
        for col in schema.get("detected_pii_fields", []):
            severity = classify_pii_severity(col)
            counts[severity] += 1

    total = sum(counts.values()) or 1
    return {
        "high_risk": counts["High"],
        "medium_risk": counts["Medium"],
        "low_risk": counts["Low"],
        "total": sum(counts.values()),
        "high_pct": round(counts["High"] / total * 100, 1),
        "medium_pct": round(counts["Medium"] / total * 100, 1),
        "low_pct": round(counts["Low"] / total * 100, 1),
    }

@app.get("/api/quality-insights")
def quality_insights() -> Dict[str, Any]:
    from mcp_server.mcp_server import auto_profile_dataset_anomalies

    insights: List[Dict[str, Any]] = []

    for urn in DATASET_REGISTRY.keys():
        result = auto_profile_dataset_anomalies(urn)
        profile = result.get("profile", {})
        table = profile.get("table", "")

        for item in profile.get("null_anomalies", []):
            insights.append({
                "type": "High null rate",
                "column": f"{table}.{item['column']}",
                "percentage": item["null_percentage"],
            })

        for item in profile.get("numeric_anomalies", []):
            pct = item.get("negative_percentage", item.get("percentage", 0))
            insights.append({
                "type": "Out of range values" if "issue" in item else "Negative values",
                "column": f"{table}.{item['column']}",
                "percentage": pct,
            })

        for item in profile.get("date_logic_anomalies", []):
            insights.append({
                "type": "Inconsistent date logic",
                "column": f"{table}.{item['col_1']}/{item['col_2']}",
                "percentage": item["percentage"],
            })

    insights.sort(key=lambda x: x["percentage"], reverse=True)

    # Эвристика, не точная научная метрика: штраф пропорционален среднему % аномалий.
    avg_pct = sum(i["percentage"] for i in insights) / len(insights) if insights else 0
    overall_score = round(max(0, 100 - avg_pct * 2))

    return {
        "overall_score": overall_score,
        "total_issues": len(insights),
        "top_issues": insights[:6],
    }

@app.get("/api/proposals")
def pending_proposals() -> List[Dict[str, Any]]:
    """Питает панель Pending Proposals — по одному патчу на карточку."""
    all_proposals = []
    for urn in DATASET_REGISTRY.keys():
        result = get_remediation_patches(urn)
        if "error" in result:
            continue
        for patch in result["patches"]:
            all_proposals.append({
                "proposal_id": patch["patch_id"],
                "dataset_urn": urn,
                "action_type": patch["patch_type"],
                "target_column": patch["target_column"],
                "description": patch["description"],
            })
    return all_proposals


@app.post("/api/proposals/{patch_id}/approve")
def approve_proposal(patch_id: str, dataset_urn: str) -> Dict[str, Any]:
    """Approve = реальное применение патча. Вызывает write-функцию НАПРЯМУЮ, не через MCP tool."""
    from mcp_server.utils.patch_applier import apply_patch
    return apply_patch(dataset_urn, patch_id, DATASET_REGISTRY)


@app.post("/api/proposals/{patch_id}/reject")
def reject_proposal(patch_id: str) -> Dict[str, Any]:
    """Reject ничего не пишет в БД — просто подтверждение для UI, что карточка убрана из очереди."""
    from mcp_server.utils.patch_applier import _append_activity_log
    from datetime import datetime, timezone

    _append_activity_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "reject",
        "patch_id": patch_id,
        "dataset_urn": None,
        "patch_type": None,
        "target_column": None,
        "rows_updated": 0,
    })
    return {"patch_id": patch_id, "status": "rejected"}


@app.post("/api/generate-pr")
def generate_pr() -> Dict[str, Any]:
    from agent.agent import main as run_governance_pr_flow
    return run_governance_pr_flow()


@app.get("/api/lineage-graph")
def lineage_graph() -> Dict[str, Any]:
    """Узлы = датасеты, рёбра = lineage-связи из discover_lineage_edges.
    Стадия (raw/staging/mart) определяется по имени таблицы для раскладки на фронте."""
    edges = discover_lineage_edges(DATASET_REGISTRY)

    def stage_of(table_name: str) -> str:
        t = table_name.lower()
        if "raw" in t:
            return "raw"
        if "staging" in t:
            return "staging"
        return "mart"

    nodes = []
    for urn, meta in DATASET_REGISTRY.items():
        columns = get_table_fields(meta["db_path"], meta["table"])
        pii_cols = detect_pii_columns(columns)
        nodes.append({
            "id": urn,
            "table": meta["table"],
            "domain": meta["domain"],
            "stage": stage_of(meta["table"]),
            "col_count": len(columns),
            "has_pii": len(pii_cols) > 0,
        })

    edge_list = [{"source": s, "target": t} for s, t in edges]
    return {"nodes": nodes, "edges": edge_list}

@app.get("/api/activity-log")
def activity_log() -> Dict[str, Any]:
    import json
    from pathlib import Path

    log_path = Path("data/activity_log.json")
    if not log_path.exists():
        return {"events": []}

    with open(log_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    return {"events": list(reversed(events))}  # самые свежие сверху