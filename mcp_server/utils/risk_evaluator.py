from typing import Dict, Any, List
from datetime import datetime

from mcp_server.utils.pii_detector import detect_pii_columns


def evaluate_dataset_risk(
    urn: str = "",
    fields: List[str] = None,
    centrality: float = 0.0,
    is_orphan: bool = False,
    last_updated_ts: float = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Calculates the aggregate risk score for a dataset.
    The signature matches the actual call in `mcp_server.py:score_dataset_risk`.
    PII is determined here based on the fields rather than being expected as pre-computed externally—
    this is the sole source of PII detection, utilizing the same `detect_pii_columns` logic used elsewhere.
    """
    fields = fields or []
    pii_found = detect_pii_columns(fields)

    stale_hours = 0.0
    if last_updated_ts:
        stale_hours = max(0.0, (datetime.now().timestamp() - last_updated_ts) / 3600.0)

    pii_score = 0.4 if pii_found else 0.0
    freshness_score = min(stale_hours / 24.0, 0.4)
    centrality_score = centrality * 0.2

    total_risk = round(min(pii_score + freshness_score + centrality_score, 1.0), 2)

    return {
        "dataset_urn": urn,
        "risk_score": total_risk,
        "has_pii": len(pii_found) > 0,
        "pii_columns": pii_found,
        "pii_fields": pii_found,  # alias: score_all_datasets_risk in mcp_server.py reads precisely this key
        "stale_hours": round(stale_hours, 2),
        "has_freshness_issue": stale_hours > 24,
        "is_orphan": is_orphan,
        "is_high_risk": total_risk >= 0.65,
    }