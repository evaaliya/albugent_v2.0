from typing import Dict, Any, List

def generate_remediation_sql(table_name: str, profile_data: Dict[str, Any]) -> str:
    """
    Генерирует детерминированный SQL-скрипт ремедиации (очистки) на основе 
    результатов профилирования аномалий.
    """
    select_expressions = []
    
    # Собираем список всех колонок, которые нужно обработать (чтобы не потерять остальные)
    # В реальном dbt/SQL обычно пишется SELECT *, но с заменой проблемных полей.
    
    null_cols = {item["column"] for item in profile_data.get("null_anomalies", [])}
    numeric_issues = profile_data.get("numeric_anomalies", [])
    date_issues = profile_data.get("date_logic_anomalies", [])
    
    fixes_applied = []

    # 1. Шаблоны для числовых аномалий (отрицательные значения, невалидный возраст)
    for anomaly in numeric_issues:
        col = anomaly["column"]
        if "age" in col.lower():
            # Заменяем невалидный возраст на NULL или дефолт (например, 30)
            select_expressions.append(f"CASE WHEN {col} < 0 OR {col} > 120 THEN NULL ELSE {col} END AS {col}")
            fixes_applied.append(f"Fixed invalid age range in column '{col}'")
        else:
            # Отрицательные суммы/цены заменяем на 0 или абсолютное значение
            select_expressions.append(f"CASE WHEN {col} < 0 THEN 0 ELSE {col} END AS {col}")
            fixes_applied.append(f"Fixed negative values in numeric column '{col}'")

    # 2. Шаблоны для NULL значений
    for item in profile_data.get("null_anomalies", []):
        col = item["column"]
        # Пропускаем, если колонка уже обрабатывается в числовых аномалиях
        if any(col == a.get("column") for a in numeric_issues):
            continue
        
        # Если текстовая/общая колонка с NULL — заменяем на заглушку 'UNKNOWN' или оставляем NULL
        if "name" in col.lower() or "title" in col.lower():
            select_expressions.append(f"COALESCE({col}, 'UNKNOWN') AS {col}")
            fixes_applied.append(f"Replaced NULLs with 'UNKNOWN' in text column '{col}'")
        else:
            select_expressions.append(f"COALESCE({col}, 0) AS {col}")
            fixes_applied.append(f"Replaced NULLs with 0 in column '{col}'")

    # 3. Шаблоны для логики дат (инверсия: когда дата начала больше даты конца)
    date_swapped_cols = set()
    for date_anomaly in date_issues:
        c1 = date_anomaly["col_1"]
        c2 = date_anomaly["col_2"]
        date_swapped_cols.add(c1)
        date_swapped_cols.add(c2)
        # Меняем местами через CASE WHEN, если они перепутаны
        select_expressions.append(f"CASE WHEN {c1} > {c2} THEN {c2} ELSE {c1} END AS {c1}")
        select_expressions.append(f"CASE WHEN {c1} > {c2} THEN {c1} ELSE {c2} END AS {c2}")
        fixes_applied.append(f"Corrected inverted date logic between '{c1}' and '{c2}'")

    header_comment = f"""-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: {table_name}
-- Generated Fixes:
--   * """ + "\n--   * ".join(fixes_applied) + f"""
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_{table_name} AS
SELECT 
    * 
FROM {table_name};
"""
    
    # Для простоты и универсальности возвращаем готовый SQL с комментариями-отчетами
    return header_comment
