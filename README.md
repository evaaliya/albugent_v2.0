# Albugent — Autonomous Data Governance Agent

Albugent is an autonomous AI agent that audits SQLite datasets for data quality issues and PII, reasons over the findings using its own judgment, and ships the results as a ready-to-review GitHub Pull Request — a deterministic SQL remediation script plus a human-readable governance report.

Built with the [Strands Agents SDK](https://strandsagents.com) on AWS Bedrock.

---

## The Problem

Data engineers spend hours manually auditing pipelines for quality and compliance issues — checking for NULLs, invalid ranges, broken date logic, PII exposure, and figuring out which downstream tables an issue actually affects. It's repetitive, judgment-heavy work that still needs to happen continuously, not just once.

Albugent automates the audit end to end: it investigates every registered dataset on its own, decides which checks to run and in what order, and produces both the fix (deterministic SQL) and the explanation (a governance report) — without a human driving each step.

---

## How It Works

Albugent runs in two phases per execution:

### Phase 1 — Deterministic Context & SQL Generation (no LLM)

1. `scan_enterprise_datasets()` scans `data/<domain>/*.db` and builds a registry of every table across every domain, keyed by a DataHub-style URN.
2. For each dataset, a set of pure-Python profilers run: null-rate analysis, numeric range checks, date-logic inversion checks, PII column detection (keyword-based), and lineage-aware risk scoring.
3. `generate_remediation_sql()` turns every detected anomaly into a safe, deterministic SQL fix (`CASE WHEN` / `COALESCE` patterns) — one `CREATE OR REPLACE TABLE cleaned_<table>` statement per dataset, with untouched columns preserved and PII columns tagged inline as SQL comments.

This half of the pipeline never touches an LLM. The SQL that ends up in the PR is 100% reproducible from the data.

### Phase 2 — Agentic Investigation & Report (Strands + Bedrock)

1. Albugent's MCP server (`mcp_server/mcp_server.py`) exposes the same profiling logic as MCP tools.
2. A Strands `Agent`, backed by Amazon Bedrock (Nova Pro), connects to that MCP server over stdio and is given a limited, read-only toolset:
   - `list_available_datasets`
   - `inspect_dataset_schema`
   - `auto_profile_dataset_anomalies`
   - `score_dataset_risk`
3. The agent decides for itself how to investigate: it typically lists all datasets, then for each one calls schema inspection, anomaly profiling, and risk scoring — but the order and reasoning are its own, not a hardcoded script.
4. After investigating every dataset, the agent composes a single consolidated governance report: a Table of Quality Variances, a Pipeline Lineage & Circuit Breaker section, and a remediation summary.
5. The agent is explicitly instructed never to write remediation SQL itself — that stays the responsibility of the deterministic Phase 1 script.

### Phase 3 — PR Delivery

The SQL artifact (Phase 1) and the governance report (Phase 2) are combined into a single Draft PR via the GitHub API. If an open Albugent PR already exists, it's updated in place instead of creating a duplicate (idempotent by branch-prefix detection).

---

## Architecture

```
┌────────────────────────────────────────────────────────────-─┐
│                          agent.py                            │
│  (entrypoint — orchestrates both phases)                     │
└───────────────┬───────────────────────────────┬──────────────┘
                │                               │
     Phase 1 (deterministic)          Phase 2 (agentic)
                 │                               │
                 ▼                               ▼
   ┌─────────────────────────-┐    ┌────────────────────────-──┐
   │  context_builder.py      │    │   Strands Agent           │
   │  - collect_governance    │    │   (Bedrock Nova Pro)      │
   │    _context()            │    │   tools = MCP tool subset │
   └─────────┬────────────────┘    └───────────┬───────────────┘
             │                                 │ stdio (MCP)
             ▼                                 ▼
   ┌────────────────────────-─┐    ┌─────────────────────────--─┐
   │ remediation_generator.py │    │   mcp_server.py            │
   │ → deterministic SQL      │    │   (FastMCP server)         │
   └─────────┬────────────────┘    └───────────┬───────────────-┘
             │                                  │
             │                          ┌─────────┴─────────----─┐
             │                          │   utils/               │
             │                          │  - anomaly_profiler    │
             │                          │  - pii_detector        │
             │                          │  - risk_evaluator      │
             │                          │  - lineage_discoverer  │
             │                          │  - graph_engine        │
             │                          │  - db_utils            │
             │                          └────────────────────────┘
             │                                    │
             └────────────────┬───────────────────┘
                               ▼
                     ┌──────────────────┐
                     │  github_utils.py │
                     │  → Draft PR      │
                     └──────────────────┘
```

---

## Repository Structure

```
albugent_v2.0/
├── .github/workflows/ci.yml       # scheduled + manual GitHub Actions run
├── docker-compose.yml
├── agent/
│   ├── agent.py                   # entrypoint — Phase 1 + Phase 2 orchestration
│   ├── dockerfile
│   ├── requirements.txt
│   └── prompts/
│       └── system_prompts.py      # GOVERNANCE_SYSTEM_PROMPT
├── context_builder/
│   └── context_builder.py         # deterministic per-dataset aggregation
├── mcp_server/
│   ├── mcp_server.py              # FastMCP server + tool definitions
│   ├── dockerfile
│   ├── requirements.txt
│   ├── models/cleaned_patients.sql  # SQL artifact output path
│   └── utils/
│       ├── db_utils.py             # get_table_fields, get_last_modified_timestamp
│       ├── github_utils.py         # create_remediation_pr (idempotent)
│       ├── graph_engine.py         # networkx betweenness centrality
│       ├── lineage_discoverer.py   # discover_lineage_edges, get_downstream_nodes
│       ├── pii_detector.py         # PII_KEYWORDS, detect_pii_columns
│       ├── anomaly_profiler.py     # profile_table_anomalies + heuristics
│       ├── risk_evaluator.py       # evaluate_dataset_risk
│       └── remediation_generator.py # generate_remediation_sql
└── data/
    ├── healthcare/                 # forking pipeline: raw → staging → 2 marts
    ├── fiction-retail/              # 10-table e-commerce schema
    └── nyc-taxi/                    # 3-stage pipeline with planted staleness
```

---

## Datasets

Three synthetic domains, each modeling a real pipeline pattern:

| Domain | Pattern | What it tests |
|---|---|---|
| `healthcare` | Forking pipeline (raw → staging → 2 marts) | Selective quality propagation — a billing issue shouldn't halt the demographics mart, and vice versa |
| `fiction-retail` | 10-table e-commerce schema | PII detection breadth, legitimate vs. erroneous NULLs (nullable-by-design foreign keys) |
| `nyc-taxi` | 3-stage pipeline (`nyc_taxi_pipeline.db`) | Freshness/staleness detection, coordinate data (negative longitude ≠ anomaly) |

Each domain's `README.md` documents its specific planted quality issues.

---

## Setup

### Prerequisites

- Docker and Docker Compose
- An AWS account with Bedrock model access (Nova Pro or your chosen model)
- A GitHub Personal Access Token with `repo` scope (for PR creation)

### Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
GH_TOKEN=your_github_personal_access_token
GITHUB_REPOSITORY=your-username/your-repo
```

### Data Files

The SQLite databases are distributed via GitHub Releases (not committed to the repo, to keep it lightweight). Download them into the matching domain folders:

```bash
mkdir -p data/healthcare data/fiction-retail data/nyc-taxi

curl -L -o data/healthcare/healthcare.db \
  "https://github.com/<owner>/<repo>/releases/download/v1.0.0/healthcare.db"
curl -L -o data/fiction-retail/fiction-retail.db \
  "https://github.com/<owner>/<repo>/releases/download/v1.0.0/fiction-retail.db"
curl -L -o data/nyc-taxi/nyc_taxi_pipeline.db \
  "https://github.com/<owner>/<repo>/releases/download/v1.0.0/nyc_taxi_pipeline.db"
```

> Note: `data/nyc-taxi/` should contain **only** `nyc_taxi_pipeline.db` — not the separate `nyc_taxi.db` clean-pipeline variant. Having both causes duplicate dataset registration (identical table names collide in the registry).

### Run

```bash
docker compose run --build --rm strands-agent
```

This will:
1. Scan all registered datasets
2. Generate the deterministic SQL remediation artifact
3. Run the agentic investigation and compile the governance report
4. Open (or update) a Draft PR on your configured repository

### CI/CD

`.github/workflows/ci.yml` runs the same flow on a daily schedule (06:00 UTC) and on manual dispatch, downloading the datasets fresh from Releases inside the runner.

---

## MCP Tools

Exposed by `mcp_server.py`, callable both by the agent (via MCP/stdio) and directly in Python:

| Tool | Purpose |
|---|---|
| `list_available_datasets` | Returns all registered dataset URNs |
| `inspect_dataset_schema` | Columns, tags, and detected PII fields for a dataset |
| `auto_profile_dataset_anomalies` | Full anomaly profile (NULLs, numeric, date-logic) + downstream lineage impact |
| `score_dataset_risk` | Combined PII + freshness + centrality risk score |
| `score_all_datasets_risk` | Aggregated risk across the whole registry |
| `execute_sql_query` | Read-only (`SELECT`/`PRAGMA` only) ad-hoc querying |
| `calculate_pipeline_centrality` | Betweenness centrality across the lineage graph |
| `get_dataset_sample` | Sample rows for manual inspection |

The Phase 2 agent is currently scoped to a subset of these (`list_available_datasets`, `inspect_dataset_schema`, `auto_profile_dataset_anomalies`, `score_dataset_risk`) — deliberately excluding `execute_sql_query` for now to keep the agent's investigation surface predictable while the tool-use architecture matures.

---

## Anomaly Detection Approach

Detection is heuristic + statistical, not hardcoded to specific column names:

- **Numeric anomalies**: negative-value checks, with an explicit exclusion list for columns where negative values are legitimate (e.g. geographic longitude)
- **Date-logic anomalies**: pairwise column comparison using `DATE()` normalization, so a `datetime` column isn't falsely flagged against a `date`-only column of the same day
- **NULL-rate classification**: a statistical threshold (currently 20%) distinguishes likely data-entry errors from nullable-by-design fields (e.g. an optional foreign key), surfaced separately as "Informational" rather than "Pending Review"
- **PII detection**: keyword-based column name matching (`name`, `email`, `phone`, `ssn`, etc.), shared between the schema inspector and the risk scorer

---

## Known Limitations

This is an active hackathon build. Documenting gaps honestly:

- **Circuit breaker logic is partially implemented.** The agent has access to `downstream_impact_nodes` via lineage data and is instructed to reason about selective halting, but full automated circuit-breaking (i.e. actually gating downstream processing) is not yet wired into a control system.
- **PII consolidation is not 100% reliable across large investigations.** With 15+ datasets and 50+ tool calls per run, the agent occasionally omits PII findings from the final consolidated report despite explicit system-prompt instructions — a known long-context recall limitation being addressed via a planned verifier-agent pattern (see Roadmap).
- **No automated test suite yet.** SQL correctness has been verified by manual execution, not CI-gated tests.
- **No idempotent dataset-registry caching.** Each run rescans datasets from disk; this is intentional for correctness (see `agent.py`'s explicit `scan_enterprise_datasets()` call) but has no caching layer.
- **Security review is in progress**, particularly around token scoping and tool-access boundaries for the agentic phase.

---

## Roadmap

- [ ] Verifier/critic agent pattern: a second agent that checks the primary agent's report against raw tool outputs (e.g. every dataset with `detected_pii_fields` has a corresponding report row) and requests corrections before the PR is opened
- [ ] Full selective circuit-breaker implementation (halt only the specific downstream datasets affected by an anomaly, not the whole pipeline)
- [ ] Per-dataset schema contracts (explicit `nullable`, `allow_negative`, column-type declarations) to reduce reliance on heuristics for known domains
- [ ] Automated SQL execution tests in CI
- [ ] Amazon Bedrock AgentCore deployment for production-grade runtime, identity, and observability
- [ ] Amazon Bedrock Guardrails integration for PII redaction and prompt-injection protection

---

## Tech Stack

- **Agent framework**: [Strands Agents SDK](https://strandsagents.com) (Apache 2.0)
- **Model**: Amazon Bedrock (Nova Pro)
- **Tool protocol**: Model Context Protocol (MCP), via `FastMCP`
- **Data layer**: SQLite
- **Lineage graph**: NetworkX (betweenness centrality)
- **PR automation**: PyGithub
- **Deployment**: Docker / Docker Compose, GitHub Actions

---


### 📄 License
This project is licensed under the Apache-2.0 License - see the LICENSE file for details.
