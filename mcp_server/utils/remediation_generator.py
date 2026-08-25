from typing import Dict, Any, List

def generate_remediation_sql(table_name: str, profile_data: Dict[str, Any], pii_columns: List[str] = None) -> str:
    pii_columns = pii_columns or []
    all_columns = profile_data.get("all_columns", [])
    null_anomalies = profile_data.get("null_anomalies", [])
    numeric_issues = profile_data.get("numeric_anomalies", [])
    date_issues = profile_data.get("date_logic_anomalies", [])

    column_expr: Dict[str, str] = {}
    fixes_applied = []

    # 1. Числовые аномалии — группируем по колонке, чтобы не задваивать
    numeric_by_col: Dict[str, List[dict]] = {}
    for anomaly in numeric_issues:
        numeric_by_col.setdefault(anomaly["column"], []).append(anomaly)

    for col, anomalies in numeric_by_col.items():
        has_age_issue = any(a.get("issue") == "invalid_age_range" for a in anomalies)
        has_negative = any("negative_count" in a for a in anomalies)

        if has_age_issue and has_negative:
            column_expr[col] = f"CASE WHEN {col} < 0 OR {col} > 120 THEN NULL ELSE {col} END"
            fixes_applied.append(f"Fixed invalid/negative age range in column '{col}'")
        elif has_age_issue:
            column_expr[col] = f"CASE WHEN {col} < 0 OR {col} > 120 THEN NULL ELSE {col} END"
            fixes_applied.append(f"Fixed invalid age range in column '{col}'")
        else:
            column_expr[col] = f"CASE WHEN {col} < 0 THEN 0 ELSE {col} END"
            fixes_applied.append(f"Fixed negative values in numeric column '{col}'")

    # 2. NULL-значения — пропускаем колонки, уже покрытые числовыми фиксами
    for item in null_anomalies:
        col = item["column"]
        if col in column_expr:
            continue
        if "name" in col.lower() or "title" in col.lower():
            column_expr[col] = f"COALESCE({col}, 'UNKNOWN')"
            fixes_applied.append(f"Replaced NULLs with 'UNKNOWN' in text column '{col}'")
        else:
            column_expr[col] = f"COALESCE({col}, 0)"
            fixes_applied.append(f"Replaced NULLs with 0 in column '{col}'")

    # 3. Инверсия дат — только для пар (ровно 2 связанные колонки).
    # 3+ связанных колонки неоднозначны — не трогаем автоматически.
    date_conditions: Dict[str, List[str]] = {}
    for date_anomaly in date_issues:
        c1, c2 = date_anomaly["col_1"], date_anomaly["col_2"]
        date_conditions.setdefault(c1, []).append(c2)
        date_conditions.setdefault(c2, []).append(c1)

    processed_pairs = set()

    for col, partners in date_conditions.items():
        if col in column_expr:
            continue
        if len(partners) > 1:
            continue
        partner = partners[0]
        pair_key = frozenset([col, partner])
        if pair_key in processed_pairs:
            continue
        processed_pairs.add(pair_key)
        column_expr[col] = f"CASE WHEN {col} > {partner} THEN {partner} ELSE {col} END"
        fixes_applied.append(f"Corrected inverted date logic between '{col}' and '{partner}'")

    for col in all_columns:
        if col not in column_expr:
            column_expr[col] = col

    if pii_columns:
        fixes_applied.append(f"Flagged PII columns for governance review: {', '.join(pii_columns)}")

    # Собираем SELECT, добавляя PII-комментарий к соответствующим строкам
    ordered_cols = all_columns if all_columns else list(column_expr.keys())
    select_lines = []
    for i, col in enumerate(ordered_cols):
        line = f"{column_expr[col]} AS {col}"
        is_last = (i == len(ordered_cols) - 1)
        if not is_last:
            line += ","
        if col in pii_columns:
            line += "  -- [PII] Contains personally identifiable information"
        select_lines.append(line)

    columns_clause = "\n   ".join(select_lines) if select_lines else "*"

    if not fixes_applied:
        fixes_applied = ["No anomalies detected — table copied as-is."]

    header_comment = f"""-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: {table_name}
-- Generated Fixes:
--   * """ + "\n--   * ".join(fixes_applied) + f"""
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_{table_name} AS
SELECT 
    {columns_clause} 
FROM {table_name};
"""
    return header_comment