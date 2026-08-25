from typing import List

PII_KEYWORDS = ["name", "ssn", "passport", "email", "medical_condition", "phone", "card", "patient", "address"]

def detect_pii_columns(columns: List[str]) -> List[str]:
    return [c for c in columns if any(k in c.lower() for k in PII_KEYWORDS)]