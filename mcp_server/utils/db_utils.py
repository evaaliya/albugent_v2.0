import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def get_table_fields(db_path: Path | str, table_name: str) -> List[str]:
    """Возвращает список названий колонок для указанной таблицы SQLite."""
    path = Path(db_path)
    if not path.exists() or not table_name:
        return []
    try:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}');")
        rows = cursor.fetchall()
        conn.close()
        return [row[1] for row in rows]
    except Exception:
        return []

def get_last_modified_timestamp(db_path: Path | str, table_name: str = "") -> float:
    path = Path(db_path)
    if not path.exists():
        return 0.0

    if table_name:
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            cols = [row[1] for row in cursor.fetchall()]
            
            time_cols = [c for c in cols if any(k in c.lower() for k in ["time", "date", "created", "updated", "pickup"])]
            
            if time_cols:
                target_col = time_cols[0]
                cursor.execute(f"SELECT MAX({target_col}) FROM '{table_name}';")
                row = cursor.fetchone()
                conn.close()
                
                if row and row[0]:
                    val = row[0]
                    # Если числовой timestamp
                    if isinstance(val, (int, float)):
                        return float(val if val > 1e11 else val * 1000)
                    # Если дата записана строкой ISO (например '2026-08-15 10:00:00')
                    if isinstance(val, str):
                        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                        return dt.timestamp() * 1000.0
        except Exception:
            pass

    # Fallback к изменению файла
    return path.stat().st_mtime * 1000.0

def profile_table_anomalies(db_path: Path | str, table_name: str) -> Dict[str, Any]:
    """Универсально профилирует таблицу SQLite на предмет NULL, отрицательных чисел и сбоев дат."""
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

        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns_info = cursor.fetchall()
        
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}';")
        total_rows = cursor.fetchone()[0]
        summary["total_rows"] = total_rows

        if total_rows == 0:
            return summary

        cols = [col[1] for col in columns_info]
        types = {col[1]: col[2].upper() for col in columns_info}

        # 1. NULL-rate
        for col in cols:
            cursor.execute(f"SELECT COUNT(*) FROM '{table_name}' WHERE \"{col}\" IS NULL OR \"{col}\" = '';")
            null_count = cursor.fetchone()[0]
            if null_count > 0:
                summary["null_anomalies"].append({
                    "column": col,
                    "null_count": null_count,
                    "null_percentage": round((null_count / total_rows) * 100.0, 2)
                })

        # 2. Отрицательные значения в числах
        numeric_cols = [c for c in cols if any(t in types[c] for t in ["INT", "FLOAT", "REAL", "NUMERIC", "DOUBLE"])]
        for col in numeric_cols:
            cursor.execute(f"SELECT COUNT(*), MIN(\"{col}\") FROM '{table_name}' WHERE \"{col}\" < 0;")
            row = cursor.fetchone()
            neg_count = row[0]
            if neg_count > 0:
                summary["numeric_anomalies"].append({
                    "column": col,
                    "negative_count": neg_count,
                    "negative_percentage": round((neg_count / total_rows) * 100.0, 2),
                    "min_value": row[1]
                })

        conn.close()
    except Exception as e:
        summary["error"] = str(e)

    return summary