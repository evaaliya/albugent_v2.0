import logging
import os
import yaml
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from github import Github, GithubException, Auth
from mcp_server.utils.graph_engine import build_and_analyze_graph
from mcp_server.utils.pii_detector import detect_pii_columns
from mcp_server.utils.anomaly_profiler import profile_table_anomalies
from mcp_server.utils.risk_evaluator import evaluate_dataset_risk
from mcp_server.utils.lineage_discoverer import discover_lineage_edges, get_downstream_nodes
from mcp_server.utils.db_utils import get_table_fields, get_last_modified_timestamp
from mcp_server.utils.remediation_generator import generate_remediation_sql


# Настройка логирования по Production стандартам
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Albugent-MCP")

# Инициализация MCP сервера
mcp = FastMCP("Albugent-DataHub-MCP")


def get_data_root() -> Path:
    """Универсальное определение каталога с данными."""
    # 1. Проверяем явную переменную окружения
    if "PROJECT_ROOT" in os.environ:
        root = Path(os.environ["PROJECT_ROOT"]).resolve()
        if (root / "data").exists():
            return root / "data"
        if any((root / d).exists() for d in ["healthcare", "fiction-retail", "nyc-taxi"]):
            return root

    # 2. Проверяем текущий рабочий каталог
    cwd = Path.cwd().resolve()
    if (cwd / "data").exists():
        return cwd / "data"
    if any((cwd / d).exists() for d in ["healthcare", "fiction-retail", "nyc-taxi"]):
        return cwd

    # 3. Резервный поиск от файла mcp_server.py
    file_dir = Path(__file__).resolve().parent
    if (file_dir.parent / "data").exists():
        return file_dir.parent / "data"
    if any((file_dir.parent / d).exists() for d in ["healthcare", "fiction-retail", "nyc-taxi"]):
        return file_dir.parent

    # По умолчанию возвращаем /app/data или /app
    fallback = Path("/app/data") if Path("/app/data").exists() else Path("/app")
    return fallback


BASE_DIR = get_data_root()


def scan_enterprise_datasets() -> Dict[str, Dict[str, Any]]:
    """Динамически сканирует директории данных и создает реестр URN без хардкода."""
    registry = {}
    target_domains = ["healthcare", "fiction-retail", "nyc-taxi"]

    logger.info(f"Scanning data root for datasets: {BASE_DIR.absolute()}")

    for domain in target_domains:
        domain_path = BASE_DIR / domain
        if not domain_path.exists():
            logger.warning(f"Domain folder not found: {domain_path.absolute()}")
            continue

        recipe_path = domain_path / "ingest.yaml"
        # Ищем все базы SQLite (*.db) внутри папки домена
        db_files = list(domain_path.glob("*.db"))

        if not db_files:
            logger.warning(f"No .db files found in domain path: {domain_path.absolute()}")

        for db_file in db_files:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name"
                    " NOT LIKE 'sqlite_%';"
                )
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()

                for table in tables:
                    urn = f"urn:li:dataset:(urn:li:dataPlatform:sqlite,{domain}.{table},PROD)"
                    registry[urn] = {
                        "domain": domain,
                        "table": table,
                        "db_path": db_file,
                        "recipe_path": recipe_path if recipe_path.exists() else None,
                    }
                    logger.info(f"Registered Dataset URN: {urn}")
            except Exception as e:
                logger.error(f"Failed to index DB {db_file}: {e}")

    return registry


DATASET_REGISTRY: Dict[str, Dict[str, Any]] = scan_enterprise_datasets()

@mcp.tool()
def list_available_datasets() -> List[Dict[str, Any]]:
    """Returns a list of all DataHub dataset URNs available for audit."""
    global DATASET_REGISTRY, BASE_DIR
    if not DATASET_REGISTRY:
        logger.info("DATASET_REGISTRY is empty. Rescanning...")
        BASE_DIR = get_data_root()
        DATASET_REGISTRY = scan_enterprise_datasets()

    return [
        {
            "urn": urn,
            "domain": meta["domain"],
            "table_name": meta["table"],
            "status": "AVAILABLE",
        }
        for urn, meta in DATASET_REGISTRY.items()
    ]


@mcp.tool()
def inspect_dataset_schema(dataset_urn: str) -> Dict[str, Any]:
    """Inspects metadata, columns, and PII tags for a given DataHub dataset URN."""
    meta = DATASET_REGISTRY.get(dataset_urn)

    if not meta:
        return {
            "error": f"URN '{dataset_urn}' not found in registry.",
            "available_urns": list(DATASET_REGISTRY.keys()),
        }

    tags = []
    if meta["recipe_path"] and meta["recipe_path"].exists():
        try:
            with open(meta["recipe_path"], "r", encoding="utf-8") as f:
                recipe_data = yaml.safe_load(f) or {}
                tags = (
                    recipe_data.get("source", {})
                    .get("config", {})
                    .get("tags", [])
                )
        except Exception as e:
            logger.error(f"Error reading recipe {meta['recipe_path']}: {e}")

    if not tags:
        if meta["domain"] == "healthcare":
            tags = ["pii", "hipaa_regulated", "quality_monitored"]
        elif meta["domain"] == "fiction-retail":
            tags = ["pci_dss", "financial_critical"]
        else:
            tags = ["public_data", "analytics"]

    columns = []
    db_path = meta["db_path"]
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info('{meta['table']}');")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f"Error reading schema for {meta['table']}: {e}")

    detected_pii = detect_pii_columns(columns)

    return {
        "urn": dataset_urn,
        "domain": meta["domain"],
        "table": meta["table"],
        "tags": tags,
        "columns": columns,
        "detected_pii_fields": detected_pii,
        "has_high_pii_risk": len(detected_pii) > 0,
    }


# 2. MCP-инструмент для полной оценки риска (PII + Freshness + Centrality)
@mcp.tool()
def calculate_pipeline_centrality() -> Dict[str, float]:
    """Calculates Betweenness Centrality metrics for all datasets in the lineage graph."""
    nodes = list(DATASET_REGISTRY.keys())
    dynamic_edges = discover_lineage_edges(DATASET_REGISTRY)
    return build_and_analyze_graph(nodes=nodes, edges=dynamic_edges)


@mcp.tool()
def score_dataset_risk(dataset_urn: str) -> Dict[str, Any]:
    """Evaluates combined risk score (PII, pipeline centrality, freshness lag) for a dataset."""
    meta = DATASET_REGISTRY.get(dataset_urn)
    if not meta:
        return {"error": f"Dataset '{dataset_urn}' not found in registry."}

    db_path = meta.get("db_path", "")
    table_name = meta.get("table", "")
    last_updated_ts = get_last_modified_timestamp(Path(db_path), table_name)#

    # Чистые вызовы из сфокусированных модулей в utils/
    fields = get_table_fields(db_path, table_name)
    centrality_map = calculate_pipeline_centrality()
    centrality = centrality_map.get(dataset_urn, 0.0)
    

    dynamic_edges = discover_lineage_edges(DATASET_REGISTRY)
    dst_nodes = {edge[1] for edge in dynamic_edges}
    is_root = dataset_urn not in dst_nodes

    return evaluate_dataset_risk(
        urn=dataset_urn,
        fields=fields,
        centrality=centrality,
        is_orphan=(centrality == 0.0 and not is_root),
        last_updated_ts=last_updated_ts
    )
#----------------------------------------------------
@mcp.tool()
def score_all_datasets_risk() -> Dict[str, Any]:
    """Calculates combined risk scores and aggregates vulnerabilities for ALL registered datasets."""
    dataset_scores = {}
    freshness_vulnerabilities = []
    pii_vulnerabilities = []
    high_risk_datasets = []

    for urn in DATASET_REGISTRY.keys():
        score_data = score_dataset_risk(urn)
        dataset_scores[urn] = score_data

        if not isinstance(score_data, dict) or "error" in score_data:
            continue

        # Собираем явный список проблем со свежестью
        if score_data.get("has_freshness_issue"):
            freshness_vulnerabilities.append({
                "urn": urn,
                "hours_stale": score_data.get("hours_stale", 0.0),
                "risk_score": score_data.get("risk_score", 0.0)
            })

        if score_data.get("has_pii"):
            pii_vulnerabilities.append({
                "urn": urn,
                "pii_fields": score_data.get("pii_fields", [])
            })

        if score_data.get("risk_score", 0.0) >= 0.65:
            high_risk_datasets.append(urn)

    return {
        "datasets": dataset_scores,
        "summary": {
            "total_evaluated": len(dataset_scores),
            "high_risk_count": len(high_risk_datasets),
            "freshness_vulnerabilities": freshness_vulnerabilities,
            "pii_vulnerabilities": pii_vulnerabilities
        }
    }
#__---------fixed version---------------------------up
@mcp.tool()
def get_dataset_sample(dataset_urn: str, limit: int = 5) -> Dict[str, Any]:
    """Retrieves column names and a sample of rows from the dataset for data profiling."""
    meta = DATASET_REGISTRY.get(dataset_urn)
    if not meta:
        return {"error": f"URN '{dataset_urn}' not found in registry."}

    db_path = meta["db_path"]
    table_name = meta["table"]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM '{table_name}' LIMIT ?;", (limit,))
        rows = cursor.fetchall()

        cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()

        return {
            "urn": dataset_urn,
            "columns": columns,
            "sample_rows": [dict(zip(columns, row)) for row in rows],
        }
    except Exception as e:
        logger.error(f"Error sampling dataset {dataset_urn}: {e}")
        return {"error": str(e), "urn": dataset_urn}


@mcp.tool()
def execute_sql_query(dataset_urn: str, query: str) -> Dict[str, Any]:
    """Executes a read-only SQL SELECT query on a dataset to perform deep data quality, staleness, or compliance audits."""
    meta = DATASET_REGISTRY.get(dataset_urn)
    if not meta:
        return {"error": f"URN '{dataset_urn}' not found in registry."}

    # Безопасность: только READ-ONLY запросы
    clean_query = query.strip()
    if not clean_query.lower().startswith("select") and not clean_query.lower().startswith("pragma"):
        return {"error": "Only read-only SELECT or PRAGMA queries are allowed."}

    db_path = meta["db_path"]

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(clean_query)
        rows = cursor.fetchall()

        col_names = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()

        return {
            "urn": dataset_urn,
            "query": query,
            "columns": col_names,
            "results": [dict(zip(col_names, row)) for row in rows],
        }
    except Exception as e:
        logger.error(f"SQL execution error on {dataset_urn}: {e}")
        return {"error": str(e), "query": query}
    
#new tool---------------------------------
@mcp.tool()
def auto_profile_dataset_anomalies(dataset_urn: str) -> Dict[str, Any]:
    """
    Универсально профилирует данные датасета без привязки к конкретной предметной области.
    Возвращает статистические аномалии (NULLs, отрицательные значения, сбои хронологии дат).
    """
    meta = DATASET_REGISTRY.get(dataset_urn)
    if not meta:
        return {"error": f"Dataset {dataset_urn} not found"}

    db_path = meta.get("db_path", "")
    table_name = meta.get("table", "")

    profile_data = profile_table_anomalies(db_path, table_name)
    lineage_downstream = get_downstream_nodes(dataset_urn, DATASET_REGISTRY)

    return {
        "dataset_urn": dataset_urn,
        "profile": profile_data,
        "downstream_impact_nodes": lineage_downstream
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")