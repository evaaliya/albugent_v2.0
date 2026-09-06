from typing import Dict, Any, List
from dataclasses import dataclass, field


@dataclass
class RemediationPatch:
    """Один атомарный, применимый по отдельности артефакт-фикс для UI."""
    patch_id: str                  # напр. "mart_billing.billing_amount.negative_fix"
    dataset_urn: str
    table_name: str
    target_column: str
    patch_type: str                # "negative_fix" | "invalid_age" | "null_fill" | "date_logic_fix" | "pii_flag"
    column_expr: str               # SQL-выражение для SELECT (напр. "CASE WHEN ... END")
    description: str
    affected_columns: List[str] = field(default_factory=list)  # для date-фиксов их две


def generate_remediation_patches(
    dataset_urn: str,
    table_name: str,
    profile_data: Dict[str, Any],
    pii_columns: List[str] = None,
) -> List[RemediationPatch]:
    """
    Единственное место, где строится маппинг колонка -> SQL-выражение.
    Возвращает список независимых патчей — по одному на аномалию/колонку.
    generate_remediation_sql() ниже просто собирает их в один SELECT.

    Колонки, помеченные профилировщиком как high_null_rate_columns (>20% NULL,
    "likely nullable by design" — напр. delivered_date для заказов в пути),
    НЕ получают null_fill патч. Высокий NULL rate там — легитимное бизнес-состояние,
    не аномалия.
    """
    pii_columns = pii_columns or []
    null_anomalies = profile_data.get("null_anomalies", [])
    high_null_rate_cols = {c["column"] for c in profile_data.get("high_null_rate_columns", [])}
    numeric_issues = profile_data.get("numeric_anomalies", [])
    date_issues = profile_data.get("date_logic_anomalies", [])

    patches: List[RemediationPatch] = []
    handled_cols: set = set()

    # 1. Числовые аномалии — группируем по колонке
    numeric_by_col: Dict[str, List[dict]] = {}
    for anomaly in numeric_issues:
        numeric_by_col.setdefault(anomaly["column"], []).append(anomaly)

    for col, anomalies in numeric_by_col.items():
        has_age_issue = any(a.get("issue") == "invalid_age_range" for a in anomalies)
        has_negative = any("negative_count" in a for a in anomalies)

        if has_age_issue:
            expr = f"CASE WHEN {col} < 0 OR {col} > 120 THEN NULL ELSE {col} END"
            desc = (
                f"Fixed invalid/negative age range in column '{col}'"
                if has_negative else
                f"Fixed invalid age range in column '{col}'"
            )
            patch_type = "invalid_age"
        else:
            expr = f"CASE WHEN {col} < 0 THEN 0 ELSE {col} END"
            desc = f"Fixed negative values in numeric column '{col}'"
            patch_type = "negative_fix"

        patches.append(RemediationPatch(
            patch_id=f"{table_name}.{col}.{patch_type}",
            dataset_urn=dataset_urn,
            table_name=table_name,
            target_column=col,
            patch_type=patch_type,
            column_expr=expr,
            description=desc,
            affected_columns=[col],
        ))
        handled_cols.add(col)

    # 2. NULL-значения — пропускаем колонки, уже покрытые числовыми фиксами
    # И пропускаем колонки, легитимно nullable by design (high_null_rate_columns)
    for item in null_anomalies:
        col = item["column"]
        if col in handled_cols:
            continue
        if col in high_null_rate_cols:
            continue  # напр. delivered_date — NULL значит "в пути", не аномалия

        if "name" in col.lower() or "title" in col.lower():
            expr = f"COALESCE({col}, 'UNKNOWN')"
            desc = f"Replaced NULLs with 'UNKNOWN' in text column '{col}'"
        else:
            expr = f"COALESCE({col}, 0)"
            desc = f"Replaced NULLs with 0 in column '{col}'"

        patches.append(RemediationPatch(
            patch_id=f"{table_name}.{col}.null_fill",
            dataset_urn=dataset_urn,
            table_name=table_name,
            target_column=col,
            patch_type="null_fill",
            column_expr=expr,
            description=desc,
            affected_columns=[col],
        ))
        handled_cols.add(col)

    # 3. Инверсия дат — только для пар (ровно 2 связанные колонки)
    date_conditions: Dict[str, List[str]] = {}
    for date_anomaly in date_issues:
        c1, c2 = date_anomaly["col_1"], date_anomaly["col_2"]
        date_conditions.setdefault(c1, []).append(c2)
        date_conditions.setdefault(c2, []).append(c1)

    processed_pairs = set()
    for col, partners in date_conditions.items():
        if col in handled_cols or len(partners) > 1:
            continue
        partner = partners[0]
        pair_key = frozenset([col, partner])
        if pair_key in processed_pairs:
            continue
        processed_pairs.add(pair_key)

        expr = f"CASE WHEN {col} > {partner} THEN {partner} ELSE {col} END"
        patches.append(RemediationPatch(
            patch_id=f"{table_name}.{col}_{partner}.date_logic_fix",
            dataset_urn=dataset_urn,
            table_name=table_name,
            target_column=col,
            patch_type="date_logic_fix",
            column_expr=expr,
            description=f"Corrected inverted date logic between '{col}' and '{partner}'",
            affected_columns=[col, partner],
        ))
        handled_cols.add(col)

    return patches


def generate_remediation_sql(table_name: str, profile_data: Dict[str, Any], pii_columns: List[str] = None) -> str:
    """
    Сохраняет прежнюю сигнатуру и поведение для agent.py / build_sql_remediation_artifact.
    Внутри теперь просто собирает единый SELECT из generate_remediation_patches().
    """
    pii_columns = pii_columns or []
    all_columns = profile_data.get("all_columns", [])

    patches = generate_remediation_patches(
        dataset_urn="",  # не нужен для сборки цельного SQL, только для UI-патчей
        table_name=table_name,
        profile_data=profile_data,
        pii_columns=pii_columns,
    )

    column_expr: Dict[str, str] = {p.target_column: p.column_expr for p in patches}
    fixes_applied = [p.description for p in patches]

    for col in all_columns:
        if col not in column_expr:
            column_expr[col] = col

    if pii_columns:
        fixes_applied.append(f"Flagged PII columns for governance review: {', '.join(pii_columns)}")

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

DROP TABLE IF EXISTS cleaned_{table_name};

CREATE TABLE cleaned_{table_name} AS
SELECT 
    {columns_clause} 
FROM {table_name};
"""
    return header_comment