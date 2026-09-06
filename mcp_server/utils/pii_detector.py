from typing import List

from typing import List

PII_KEYWORDS = ["name", "ssn", "passport", "email", "medical_condition", "phone",
                "card", "patient", "address", "medication"]

# High: прямая финансовая/юридическая идентификация
# Medium: контактные данные / чувствительная медицинская информация
# Low: обобщённые идентификаторы (имя, роль)
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
    """Первое совпадение по PII_SEVERITY определяет уровень.
    Порядок словаря важен: специфичные ключи (ssn) идут раньше общих (name),
    чтобы колонка вроде 'patient_ssn' классифицировалась как High, не Low."""
    col_lower = column.lower()
    for keyword, severity in PII_SEVERITY.items():
        if keyword in col_lower:
            return severity
    return "Low"