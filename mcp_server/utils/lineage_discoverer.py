import os
import sqlite3
from typing import Dict, List, Tuple, Any


def discover_lineage_edges(dataset_registry: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Dynamically identifies lineage between registered datasets
    based on foreign keys or layer naming conventions.
    """
    edges = []
    
    # 1. Trying to find explicit foreign keys in SQLite
    for src_urn, src_meta in dataset_registry.items():
        db_path = src_meta.get("db_path")
        table = src_meta.get("table")
        
        if not db_path or not os.path.exists(db_path):
            continue
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA foreign_key_list('{table}');")
            fk_list = cursor.fetchall()
            for fk in fk_list:
                target_table = fk[2]
                for dst_urn, dst_meta in dataset_registry.items():
                    if dst_meta.get("table") == target_table:
                        edges.append((src_urn, dst_urn))
            conn.close()
        except Exception:
            pass

    # 2. Implicit fallback: linking layers (raw -> staging -> mart) within a single domain.
    if not edges:
        grouped = {}
        for urn in dataset_registry.keys():
            domain = urn.split(".")[0] if "." in urn else "default"
            grouped.setdefault(domain, []).append(urn)
        
        for domain, urns in grouped.items():
            raws = [u for u in urns if "raw" in u]
            stagings = [u for u in urns if "staging" in u]
            marts = [u for u in urns if "mart" in u]
            
            for r in raws:
                for s in stagings:
                    edges.append((r, s))
            for s in stagings:
                for m in marts:
                    edges.append((s, m))
                    
    return list(set(edges))

def get_downstream_nodes(dataset_urn: str, dataset_registry: Dict[str, Any]) -> List[str]:
    """Returns a list of all URNs located downstream from the current URN."""
    # Get dynamic links [(src_urn, dst_urn), ...]
    edges = discover_lineage_edges(dataset_registry)
    
    downstream = []
    for src, dst in edges:
        if src == dataset_urn:
            downstream.append(dst)
            
    return downstream