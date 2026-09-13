from typing import List

from typing import List

PII_KEYWORDS = ["name", "ssn", "passport", "email", "medical_condition", "phone",
                "card", "patient", "address", "medication"]

# High: direct financial/legal identification
# Medium: contact details / sensitive medical information
# Low: generalized identifiers (name, role)
PII_SEVERITY = {
    "ssn": "High",
    "passport": "High",
    "card": "High",
    "email": "Medium",
    "phone": "Medium",
    "medical_condition": "Medium",
    "medication": "Medium",
    "address": "Medium",
    "name": "Low",
    "patient": "Low",
}


def detect_pii_columns(columns: List[str]) -> List[str]:
    return [c for c in columns if any(k in c.lower() for k in PII_KEYWORDS)]


def classify_pii_severity(column: str) -> str:
    """The first PII_SEVERITY match determines the level.
    The dictionary order matters: specific keys (ssn) come before general ones (name)
    so that a column like 'patient_ssn' is classified as High rather than Low."""
    col_lower = column.lower()
    for keyword, severity in PII_SEVERITY.items():
        if keyword in col_lower:
            return severity
    return "Low"