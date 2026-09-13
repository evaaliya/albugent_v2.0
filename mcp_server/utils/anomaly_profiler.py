#anomaly_profiler.py
import sqlite3
import re
import logging; logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Dict, List, Any, Optional

COORDINATE_KEYWORDS = ["longitude", "latitude"]

# Roles for pairwise date comparison. A column is considered a pair with another ONLY if
# one falls under START and the other under END. Simply "looking like a date" is not enough
# (this was the bug: trip_date matched with tpep_dropoff_datetime simply because
# both contained "date"/"time", even though trip_date is a derived aggregate date,
# not a paired timestamp).
START_KEYWORDS = ["admission", "start", "pickup", "shipped", "created", "signup", "opened"]
END_KEYWORDS = ["discharge", "end", "dropoff", "delivered", "updated", "closed", "return"]


def _is_date_like_column(col: str) -> bool:
    """A general "does this look like a date?" check — used as a preliminary filter."""
    col_lower = col.lower()

    non_date_suffixes = ["_type", "_id", "_status", "_category", "_code", "_flag"]
    if any(col_lower.endswith(s) for s in non_date_suffixes):
        return False

    substring_keywords = ["date", "time", "created", "updated", "admission", "discharge"]
    if any(k in col_lower for k in substring_keywords):
        return True

    boundary_keywords = ["start", "end"]
    return any(re.search(rf"(^|_){k}($|_)", col_lower) for k in boundary_keywords)


def _get_date_role(col: str) -> Optional[str]:
    """Returns 'start', 'end', or None. None indicates that the column does not participate
    in a paired date-logic comparison at all (e.g., aggregate/derived dates
    like trip_date, unpaired created_at, etc.)."""
    col_lower = col.lower()
    if any(k in col_lower for k in START_KEYWORDS):
        return "start"
    if any(k in col_lower for k in END_KEYWORDS):
        return "end"
    return None


def profile_table_anomalies(db_path: Path | str, table_name: str) -> Dict[str, Any]:
    """
    Universally profiles ANY SQLite table for mathematical and logical anomalies.
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

        # 1. Checking for NULL / empty values ​​across ALL columns
        NULL_RATE_THRESHOLD = 20.0  # % — above this value, NULL is considered legitimate-by-design, not an anomaly

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

        # 2. Checking for numerical anomalies (Negative values ​​and invalid age)
        for col in cols:
            if any(k in col.lower() for k in COORDINATE_KEYWORDS):
                pass
            else:
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

        # 3. Check for date inversion — only between explicit start/end pairs,
        # not between any two date-like columns (see START_KEYWORDS/END_KEYWORDS above)
        date_cols = [c for c in cols if _is_date_like_column(c)]
        start_cols = [c for c in date_cols if _get_date_role(c) == "start"]
        end_cols = [c for c in date_cols if _get_date_role(c) == "end"]

        for c1 in start_cols:
            for c2 in end_cols:
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