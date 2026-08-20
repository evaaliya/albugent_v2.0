import json
from pathlib import Path
from typing import Dict, Any, List

from mcp_server.utils.graph_engine import build_and_analyze_graph
from mcp_server.utils.pii_detector import evaluate_dataset_risk, profile_table_anomalies
from mcp_server.utils.lineage_discoverer import discover_lineage_edges
from mcp_server.utils.db_utils import get_table_fields, get_last_modified_timestamp

def collect_governance_context(dataset_registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Детерминированный сборщик метаданных и аномалий.
    Пробегает по всей системе за миллисекунды без использования LLM.
    """
    # 1. Построение графа Lineage и расчет Centrality
    edges = discover_lineage_edges(dataset_registry)
    nodes = list(dataset_registry.keys())
    centrality_map = build_and_analyze_graph(nodes, edges)

    datasets_payload = []

    # 2. Профилирование каждого датасета
    for urn, meta in dataset_registry.items():
        db_path = meta.get("db_path", "")
        table_name = meta.get("table", "")

        # Статистический профиль
        profile = profile_table_anomalies(db_path, table_name)
        
        # Зависимости Downstream
        downstream = [dst for src, dst in edges if src == urn]
        
        # Вычисление риска
        centrality = centrality_map.get(urn, 0.0)
        risk_data = evaluate_dataset_risk(
            dataset_urn=urn,
            metadata={
                "pii_columns": meta.get("pii_columns", []),
                "stale_hours": meta.get("stale_hours", 0),
                "centrality": centrality
            }
        )

        datasets_payload.append({
            "urn": urn,
            "table_name": table_name,
            "centrality": round(centrality, 4),
            "risk_score": risk_data.get("risk_score", 0.0),
            "is_high_risk": risk_data.get("is_high_risk", False),
            "pii_columns": meta.get("pii_columns", []),
            "downstream_nodes": downstream,
            "statistical_profile": profile
        })

    return {
        "lineage_edges": edges,
        "datasets": datasets_payload
    }