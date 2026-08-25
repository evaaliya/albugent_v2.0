import json
import time
from pathlib import Path
from typing import Dict, Any, List

from mcp_server.utils.graph_engine import build_and_analyze_graph
from mcp_server.utils.lineage_discoverer import discover_lineage_edges

from mcp_server.utils.pii_detector import detect_pii_columns
from mcp_server.utils.anomaly_profiler import profile_table_anomalies
from mcp_server.utils.risk_evaluator import evaluate_dataset_risk
from mcp_server.utils.db_utils import get_table_fields, get_last_modified_timestamp

def collect_governance_context(dataset_registry: Dict[str, Any]) -> Dict[str, Any]:
    edges = discover_lineage_edges(dataset_registry)
    nodes = list(dataset_registry.keys())
    centrality_map = build_and_analyze_graph(nodes, edges)

    datasets_payload = []
    now_ms = time.time() * 1000.0

    for urn, meta in dataset_registry.items():
        db_path = meta.get("db_path", "")
        table_name = meta.get("table", "")

        profile = profile_table_anomalies(db_path, table_name)
        fields = get_table_fields(db_path, table_name)
        pii_columns = detect_pii_columns(fields)

        last_updated_ts = get_last_modified_timestamp(db_path, table_name)
        stale_hours = round(max((now_ms - last_updated_ts) / (1000.0 * 3600.0), 0.0), 2)

        downstream = [dst for src, dst in edges if src == urn]
        centrality = centrality_map.get(urn, 0.0)

        risk_data = evaluate_dataset_risk(
            dataset_urn=urn,
            metadata={
                "pii_columns": pii_columns,
                "stale_hours": stale_hours,
                "centrality": centrality
            }
        )

        datasets_payload.append({
            "urn": urn,
            "table_name": table_name,
            "centrality": round(centrality, 4),
            "risk_score": risk_data.get("risk_score", 0.0),
            "is_high_risk": risk_data.get("is_high_risk", False),
            "pii_columns": pii_columns,
            "stale_hours": stale_hours,
            "downstream_nodes": downstream,
            "statistical_profile": profile
        })

    return {"lineage_edges": edges, "datasets": datasets_payload}