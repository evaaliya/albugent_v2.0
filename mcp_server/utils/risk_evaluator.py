from typing import Dict, Any

def evaluate_dataset_risk(dataset_urn: str = "", metadata: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """
    Вычисляет интегральный скор риска датасета.
    Принимает аргументы как dataset_urn, так и urn за счет **kwargs.
    """
    # Если передали urn вместо dataset_urn
    urn = dataset_urn or kwargs.get("urn", "")
    metadata = metadata or {}

    pii_found = metadata.get("pii_columns", [])
    freshness_hours = metadata.get("stale_hours", 0)
    centrality = metadata.get("centrality", 0.0)

    pii_score = 0.4 if pii_found else 0.0
    freshness_score = min(freshness_hours / 24.0, 0.4)
    centrality_score = centrality * 0.2

    total_risk = round(min(pii_score + freshness_score + centrality_score, 1.0), 2)

    return {
        "dataset_urn": urn,
        "risk_score": total_risk,
        "has_pii": len(pii_found) > 0,
        "pii_columns": pii_found,
        "stale_hours": freshness_hours,
        "has_freshness_issue": freshness_hours > 24,   
        "is_high_risk": total_risk >= 0.65
    }