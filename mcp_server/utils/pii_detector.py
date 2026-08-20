import sqlite3
from pathlib import Path
from typing import Dict, List, Any

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
        "null_anomalies": [],
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

        # 1. Проверка NULL / Пустых значений по ВСЕМ колонкам
        for col in cols:
            cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\" WHERE \"{col}\" IS NULL OR CAST(\"{col}\" AS TEXT) = '' OR CAST(\"{col}\" AS TEXT) = 'NULL';")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                summary["null_anomalies"].append({
                    "column": col,
                    "null_count": null_count,
                    "null_percentage": round((null_count / total_rows) * 100.0, 2)
                })

        # 2. Проверка числовых аномалий (Отрицательные значения и Невалидный возраст)
        for col in cols:
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
            except Exception:
                pass

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
                except Exception:
                    pass

        # 3. Проверка инверсии дат (admission > discharge, start > end)
        date_cols = [c for c in cols if any(k in c.lower() for k in ["date", "time", "created", "updated", "admission", "discharge", "start", "end"])]
        if len(date_cols) >= 2:
            for i in range(len(date_cols)):
                for j in range(i + 1, len(date_cols)):
                    c1, c2 = date_cols[i], date_cols[j]
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\" WHERE \"{c1}\" > \"{c2}\" AND \"{c1}\" IS NOT NULL AND \"{c2}\" IS NOT NULL AND \"{c1}\" != '' AND \"{c2}\" != '';")
                        swapped_count = cursor.fetchone()[0]
                        if swapped_count > 0:
                            summary["date_logic_anomalies"].append({
                                "col_1": c1,
                                "col_2": c2,
                                "inverted_rows_count": swapped_count,
                                "percentage": round((swapped_count / total_rows) * 100.0, 2)
                            })
                    except Exception:
                        pass

        conn.close()
    except Exception as e:
        summary["error"] = str(e)

    return summary


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
        "is_high_risk": total_risk >= 0.65
    }