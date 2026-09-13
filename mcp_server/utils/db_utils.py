import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def get_table_fields(db_path: Path | str, table_name: str) -> List[str]:
    """Returns a list of column names for the specified SQLite table."""
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
                    # if numeric timestamp
                    if isinstance(val, (int, float)):
                        return float(val if val > 1e11 else val * 1000)
                    # If the date is recorded as an ISO string (e.g., '2026-08-15 10:00:00')
                    if isinstance(val, str):
                        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
                        return dt.timestamp() * 1000.0
        except Exception:
            pass

    # Fallback to file change
    return path.stat().st_mtime * 1000.0