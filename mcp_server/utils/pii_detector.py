import time
from typing import List, Dict, Any

PII_KEYWORDS = ["name", "ssn", "passport", "email", "patient", "driver", "credit_card", "license"]

def evaluate_dataset_risk(
    urn: str,
    fields: List[str],
    centrality: float,
    is_orphan: bool,
    last_updated_ts: float = 0.0
) -> Dict[str, Any]:
    """
    Рассчитывает комбинированный риск датасета (PII + свежесть + связность + сирота).
    """
    pii_fields = [f for f in fields if any(kw in f.lower() for kw in PII_KEYWORDS)]
    has_pii = len(pii_fields) > 0

    hours_stale = 0.0
    has_freshness_issue = False
    if last_updated_ts > 0:
        hours_stale = (time.time() - (last_updated_ts / 1000.0)) / 3600.0
        if hours_stale > 24.0:
            has_freshness_issue = True

    # Формула взвешенного риска
    risk_score = min(
        1.0,
        (0.4 * centrality) + 
        (0.4 if has_pii else 0.0) + 
        (0.2 if is_orphan else 0.0) + 
        (0.1 if has_freshness_issue else 0.0)
    )

    return {
        "urn": urn,
        "risk_score": round(risk_score, 3),
        "has_pii": has_pii,
        "pii_fields": pii_fields,
        "is_orphan": is_orphan,
        "has_freshness_issue": has_freshness_issue,
        "hours_stale": round(hours_stale, 1)
    }