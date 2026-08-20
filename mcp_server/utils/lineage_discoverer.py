import os
import sqlite3
from typing import Dict, List, Tuple, Any


def discover_lineage_edges(dataset_registry: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Динамически выявляет связи (lineage) между зарегистрированными датасетами
    на основе внешних ключей (Foreign Keys) или конвенции наименования слоев.
    """
    edges = []
    
    # 1. Пробуем найти явные Foreign Keys в SQLite
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

    # 2. Неявный fallback: связываем слои raw -> staging -> mart внутри одного домена
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

def get_downstream_nodes(dataset_urn: str) -> List[str]:
    """Возвращает список всех URN, которые находятся ниже по истоку (downstream) от текущего URN."""
    # Получаем динамические связи [(src_urn, dst_urn), ...]
    from mcp_server import DATASET_REGISTRY # или передаем registry
    edges = discover_lineage_edges(DATASET_REGISTRY)
    
    downstream = []
    for src, dst in edges:
        if src == dataset_urn:
            downstream.append(dst)
            
    return downstream