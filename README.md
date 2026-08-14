# 🤖 Albugent 2.0: Autonomous Data Governance Agent Engine

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/Framework-AWS_Strands_SDK-orange)](https://github.com/aws/strands)
[![Protocol](https://img.shields.io/badge/Protocol-MCP_(Model_Context_Protocol)-green)](#architecture)
[![Model](https://img.shields.io/badge/LLM-AWS_Bedrock_Nova_Pro-purple)](#architecture)

**Albugent 2.0** is an autonomous governance agent framework that dynamically evaluates dataset risk, analyzes lineage graphs, detects PII fields, and manages automated remediation via GitHub Pull Requests—featuring interactive **Human-in-the-Loop (HITL)** controls and a **Rich Terminal UI**.

---

## 🏗️ Architecture Overview

                      ┌───────────────────────────┐
                      │   AWS Bedrock (Nova Pro)  │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
                                    Финал близко! ✨ README.md — это лицо репозитория, особенно для жюри и участников хакатона. Он должен мгновенно объяснять архитектуру, показывть стек (Strands + Bedrock + MCP) и давать четкую инструкцию по запуску.

Создадим сочный, аккуратно структурированный README.md.

Обновляем README.md
Вставь этот текст в файл README.md в корне проекта:

Markdown
# 🤖 Albugent 2.0: Autonomous Data Governance Agent Engine

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Framework](https://img.shields.io/badge/Framework-AWS_Strands_SDK-orange)](https://github.com/aws/strands)
[![Protocol](https://img.shields.io/badge/Protocol-MCP_(Model_Context_Protocol)-green)](#architecture)
[![Model](https://img.shields.io/badge/LLM-AWS_Bedrock_Nova_Pro-purple)](#architecture)

**Albugent 2.0** is an autonomous governance agent framework that dynamically evaluates dataset risk, analyzes lineage graphs, detects PII fields, and manages automated remediation via GitHub Pull Requests—featuring interactive **Human-in-the-Loop (HITL)** controls and a **Rich Terminal UI**.

---

## 🏗️ Architecture Overview

                      ┌───────────────────────────┐
                      │   AWS Bedrock (Nova Pro)  │
                      └─────────────┬─────────────┘
                                    │
                                    ▼
┌───────────────────┐     ┌───────────────────────────┐     ┌───────────────────┐
│  GitHub Engine    │ ◄───┤   AWS Strands Agent Loop  ├────►│  Rich Terminal UI │
│ (Auto Remediation)│     └─────────────┬─────────────┘     │   (Interactive)   │
└───────────────────┘                   │                   └───────────────────┘
                                        │ (Stdio Client)
                                        ▼
                          ┌───────────────────────────┐
                          │    Custom MCP Server      │
                          │ - NetworkX Graph Engine   │
                          │ - Regex PII Risk Scorer   │
                          └───────────────────────────┘


### Key Modules:
* **AWS Strands SDK:** Core agent orchestration layer managing tool calling, reasoning, and context.
* **Model Context Protocol (MCP) Server:** Isolated microservice serving risk-scoring models and graph centrality algorithms (`igraph`/`NetworkX`).
* **Human-In-The-Loop (HITL) Safety:** Granular intervention logic that halts execution and requests operator confirmation before modifying remote repositories when critical risks are detected.
* **Rich UI Engine:** Terminal formatting with interactive spinners, decision panels, and color-coded risk tables.

---

## ⚡ Features

- 🔍 **Lineage Analysis:** Computes graph centrality for datasets to identify single points of failure.
- 🛡️ **PII Risk Scoring:** Scans schema definitions for sensitive data exposure (SSN, patient details, financial data).
- 🤝 **HITL Workflow:** Blocks high-risk automated deployments until human authorization is granted (`y/n`).
- 🚀 **Automated PR Remediation:** Programmatically generates isolated remediation branches and triggers GitHub Pull Requests.
- 🐳 **Docker-First Architecture:** Fully containerized setup via Docker Compose for seamless deployment.

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- AWS Bedrock Credentials
- GitHub Personal Access Token (`repo` permissions)

### 2. Environment Configuration
Clone the repository and create your `.env` file:

```bash
cp .env.example .env


Fill in your environment credentials:

AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
GITHUB_TOKEN=ghp_your_personal_access_token
GITHUB_REPOSITORY=evaaliya/albugent_v2.0

3. Run with Interactive Terminal (HITL Enabled)
To enable real-time operator prompts in the console, launch using docker compose run:

docker compose run --rm --build strands-agent


🎮 Interactive Demo Flow
Autonomous Audit: The agent queries the MCP server, builds lineage graphs, and outputs dataset evaluations.
Decision Rendering: A styled decision panel outlines identified risks and required actions.
Operator Intervention (HITL):

Do you authorize automated remediation and GitHub PR creation? [y/n]:

Automated PR Dispatch: Selecting y creates a new branch and submits a live Pull Request on GitHub.

📄 License
Distributed under the Apache 2.0 License. See LICENSE for more information.

---

