import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from mcp_server.utils.remediation_generator import generate_remediation_patches
from mcp_server.utils.anomaly_profiler import profile_table_anomalies
from mcp_server.utils.pii_detector import detect_pii_columns
from mcp_server.utils.db_utils import get_table_fields

ACTIVITY_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "activity_log.json"


def _append_activity_log(entry: Dict[str, Any]) -> None:
    """Дописывает одну запись в лог. Не бросает исключение наружу —
    сбой логирования не должен ронять сам apply."""
    try:
        log = []
        if ACTIVITY_LOG_PATH.exists():
            with open(ACTIVITY_LOG_PATH, "r", encoding="utf-8") as f:
                log = json.load(f)
        log.append(entry)
        log = log[-100:]  # держим последние 100 событий, не растим файл бесконечно
        with open(ACTIVITY_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception:
        pass


def apply_patch(dataset_urn: str, patch_id: str, dataset_registry: Dict[str, Any]) -> Dict[str, Any]:
    """
    НЕ MCP tool. Вызывается напрямую backend-эндпоинтом по клику "Применить" в UI.
    LLM/агент не имеет доступа к этой функции ни при каких условиях.
    """
    meta = dataset_registry.get(dataset_urn)
    if not meta:
        return {"error": f"URN '{dataset_urn}' not found"}

    profile_data = profile_table_anomalies(meta["db_path"], meta["table"])
    columns = get_table_fields(meta["db_path"], meta["table"])
    pii_cols = detect_pii_columns(columns)
    patches = generate_remediation_patches(dataset_urn, meta["table"], profile_data, pii_cols)

    target = next((p for p in patches if p.patch_id == patch_id), None)
    if not target:
        return {"error": f"Patch '{patch_id}' not found or already resolved"}

    try:
        conn = sqlite3.connect(meta["db_path"])
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE "{meta["table"]}" SET "{target.target_column}" = {target.column_expr};'
        )
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
    except Exception as e:
        return {"error": str(e), "patch_id": patch_id}

    _append_activity_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "approve",
        "patch_id": patch_id,
        "dataset_urn": dataset_urn,
        "patch_type": target.patch_type,
        "target_column": target.target_column,
        "rows_updated": rows_affected,
    })

    return {"patch_id": patch_id, "status": "applied", "rows_updated": rows_affected}