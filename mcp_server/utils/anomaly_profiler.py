import sqlite3
import re
import logging; logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Dict, List, Any

COORDINATE_KEYWORDS = ["longitude", "latitude"]

def _is_date_like_column(col: str) -> bool:
    col_lower = col.lower()

    # Явно НЕ дата, даже если содержит date-подобное слово (admission_type, date_type_id и т.п.)
    non_date_suffixes = ["_type", "_id", "_status", "_category", "_code", "_flag"]
    if any(col_lower.endswith(s) for s in non_date_suffixes):
        return False

    substring_keywords = ["date", "time", "created", "updated", "admission", "discharge"]
    if any(k in col_lower for k in substring_keywords):
        return True

    boundary_keywords = ["start", "end"]
    return any(re.search(rf"(^|_){k}($|_)", col_lower) for k in boundary_keywords)


def profile_table_anomalies(db_path: Path | str, table_name: str) -> Dict[str, Any]:
    """
    Универсально профилирует ЛЮБУЮ таблицу SQLite на предмет математических и логических аномалий.
    """
    path = Path(db_path)
    if not path.exists() or not table_name:
        return {"error": "Database file or table name missing."}

    summary = {
        "table": table_name,
        "total_rows": 0,
        "all_columns": [],
        "null_anomalies": [],
        "high_null_rate_columns": [],
        "numeric_anomalies": [],
        "date_logic_anomalies": []
    }

    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info(\"{table_name}\");")
        columns_info = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\";") 
        total_rows = cursor.fetchone()[0]
        summary["total_rows"] = total_rows

        if total_rows == 0:
            conn.close()
            return summary

        cols = [col[1] for col in columns_info]
        summary["all_columns"] = cols

        # 1. Проверка NULL / Пустых значений по ВСЕМ колонкам
        NULL_RATE_THRESHOLD = 20.0  # % — выше этого NULL считается legitimate-by-design, не аномалией

        for col in cols:
                   cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\" WHERE \"{col}\" IS NULL OR CAST(\"{col}\" AS TEXT) = '' OR CAST(\"{col}\" AS TEXT) = 'NULL';")
                   null_count = cursor.fetchone()[0]
                   if null_count > 0:
                       null_percentage = round((null_count / total_rows) * 100.0, 2)
                       entry = {
                           "column": col,
                           "null_count": null_count,
                           "null_percentage": null_percentage
                     }
                       if null_percentage > NULL_RATE_THRESHOLD:
                           entry["likely_nullable_by_design"] = True
                           summary.setdefault("high_null_rate_columns", []).append(entry)
                       else:
                           summary["null_anomalies"].append(entry)

        # 2. Проверка числовых аномалий (Отрицательные значения и Невалидный возраст)
        for col in cols:
            #coordinates (longitude/latitude)
            if any(k in col.lower() for k in COORDINATE_KEYWORDS):
                pass #passing negaive-check for this section
            else:
            # Проверяем на отрицательные числа (например, billing_amount < 0)
                try:
                    cursor.execute(f"SELECT COUNT(*), MIN(CAST(\"{col}\" AS REAL)) FROM \"{table_name}\" WHERE CAST(\"{col}\" AS REAL) < 0;")
                    row = cursor.fetchone()
                    neg_count = row[0]
                    if neg_count > 0 and row[1] is not None:
                        summary["numeric_anomalies"].append({
                        "column": col,
                        "negative_count": neg_count,
                        "negative_percentage": round((neg_count / total_rows) * 100.0, 2),
                        "min_value": row[1]
                    })
                except Exception as e:
                    logger.warning(f"Anomaly check failed on column '{col}': {e}")

            # Специальная проверка для возраста (age < 0 или age > 120)
            if "age" in col.lower():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\" WHERE CAST(\"{col}\" AS REAL) < 0 OR CAST(\"{col}\" AS REAL) > 120;")
                    invalid_age_count = cursor.fetchone()[0]
                    if invalid_age_count > 0:
                        summary["numeric_anomalies"].append({
                            "column": col,
                            "issue": "invalid_age_range",
                            "invalid_count": invalid_age_count,
                            "percentage": round((invalid_age_count / total_rows) * 100.0, 2)
                        })
                except Exception as e:
                    logger.warning(f"Anomaly check failed on column '{col}': {e}")

        # 3. Проверка инверсии дат (admission > discharge, start > end)
        date_cols = [c for c in cols if _is_date_like_column(c)]
        if len(date_cols) >= 2:
            for i in range(len(date_cols)):
                for j in range(i + 1, len(date_cols)):
                    c1, c2 = date_cols[i], date_cols[j]
                    try:
                        cursor.execute(
    f"SELECT COUNT(*) FROM \"{table_name}\" "
    f"WHERE DATE(\"{c1}\") > DATE(\"{c2}\") "
    f"AND \"{c1}\" IS NOT NULL AND \"{c2}\" IS NOT NULL "
    f"AND \"{c1}\" != '' AND \"{c2}\" != '';"
)
                        swapped_count = cursor.fetchone()[0]
                        if swapped_count > 0:
                            summary["date_logic_anomalies"].append({
                                "col_1": c1,
                               "col_2": c2,
                                "inverted_rows_count": swapped_count,
                                "percentage": round((swapped_count / total_rows) * 100.0, 2)
                            })
                    except Exception as e:
                        logger.warning(f"Anomaly check failed between columns '{c1}' and '{c2}': {e}")

        conn.close()
    except Exception as e:
        summary["error"] = str(e)

    return summary
