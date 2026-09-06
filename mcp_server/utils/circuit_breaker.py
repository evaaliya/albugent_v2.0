from typing import Dict, Any, List, Tuple
from mcp_server.utils.db_utils import get_table_fields
HALT_THRESHOLD_ROWS = 100  # порог "значимой" аномалии — настраиваемо

def compute_circuit_breaker_status(
    dataset_registry: Dict[str, Any],
    profiles: Dict[str, Dict[str, Any]],
    edges: List[Tuple[str, str]],
) -> Dict[str, str]:
    directly_halted: Dict[str, set] = {}  # urn -> set затронутых колонок
    has_any_finding = set()

    for urn, profile in profiles.items():
        affected_cols = set()
        for a in profile.get("numeric_anomalies", []):
            if a.get("negative_count", 0) >= HALT_THRESHOLD_ROWS or a.get("invalid_count", 0) >= HALT_THRESHOLD_ROWS:
                affected_cols.add(a["column"])
        for a in profile.get("null_anomalies", []):
            if a.get("null_count", 0) >= HALT_THRESHOLD_ROWS:
                affected_cols.add(a["column"])
        for a in profile.get("date_logic_anomalies", []):
            if a.get("inverted_rows_count", 0) >= HALT_THRESHOLD_ROWS:
                affected_cols.add(a["col_1"])
                affected_cols.add(a["col_2"])

        if profile.get("numeric_anomalies") or profile.get("null_anomalies") or profile.get("date_logic_anomalies"):
            has_any_finding.add(urn)
        if affected_cols:
            directly_halted[urn] = affected_cols

    downstream_map: Dict[str, List[str]] = {}
    for src, dst in edges:
        downstream_map.setdefault(src, []).append(dst)

    status = {urn: "OK" for urn in dataset_registry}

    def get_columns(urn: str) -> set:
        meta = dataset_registry.get(urn, {})
        db_path, table = meta.get("db_path"), meta.get("table")
        return set(get_table_fields(db_path, table)) if db_path and table else set()

    def propagate(urn: str, affected_cols: set, visited: set):
        if urn in visited:
            return
        visited.add(urn)
        status[urn] = "HALTED"
        for dst in downstream_map.get(urn, []):
            dst_cols = get_columns(dst)
            overlap = affected_cols & dst_cols
            if overlap:  # только если проблемная колонка реально есть в downstream-таблице
                propagate(dst, overlap, visited)

    for urn, cols in directly_halted.items():
        propagate(urn, cols, set())

    for urn in has_any_finding:
        if status[urn] == "OK":
            status[urn] = "MONITOR"

    return status