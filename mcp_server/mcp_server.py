import sys
import os
from typing import List, Tuple
try:
    from fastmcp import FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

# Импортируем утилиты
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.graph_engine import build_and_analyze_graph
from utils.pii_detector import evaluate_dataset_risk

mcp = FastMCP("Albugent-Governance-Analytics-Engine")

@mcp.tool()
async def analyze_lineage_graph(nodes: List[str], edges: List[Tuple[str, str]]) -> dict:
    """
    Принимает узлы датасетов и ребра lineage-связей.
    Возвращает Betweenness Centrality для каждого узла.
    """
    centrality = build_and_analyze_graph(nodes, edges)
    return {"centrality_scores": centrality}

@mcp.tool()
async def score_dataset_risk(
    urn: str,
    fields: List[str],
    centrality: float,
    is_orphan: bool,
    last_updated_ts: float = 0.0
) -> dict:
    """
    Рассчитывает итоговый показатель риска (risk_score) для датасета.
    """
    return evaluate_dataset_risk(urn, fields, centrality, is_orphan, last_updated_ts)

if __name__ == "__main__":
    mcp.run(transport="stdio")