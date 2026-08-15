# 🤖 Albugent 2.0: Autonomous Data Governance Engine

> An enterprise-grade Data Governance & Lineage Audit Agent powered by **AWS Strands SDK**, **Custom Model Context Protocol (MCP) Server**, and **AWS Bedrock (Amazon Nova Pro)** with Human-In-The-Loop (HITL) protection.

---

## 🌟 Key Features

* **🕸️ Graph-Based Lineage Analysis:** Calculates *Betweenness Centrality* using `NetworkX` to spot high-impact pipeline nodes.
* **🛡️ Automated PII & Risk Scoring:** Detects sensitive data fields (SSN, Passport, Email) and calculates aggregated dataset risk scores.
* **🔌 Native MCP Architecture:** Standardized communication between the agent and custom governance tools via Stdio MCP Transport.
* **🚀 Human-In-The-Loop (HITL) Remediation:** Requests human operator authorization before automatically generating GitHub Pull Requests for mitigation.
* **🐳 Fully Containerized:** Built with Docker Compose and Rich Terminal UI for seamless environment setup.

---

## 🛠️ Tech Stack

* **AI Framework:** AWS Strands SDK
* **LLM Engine:** AWS Bedrock (`amazon.nova-pro-v1:0`)
* **Protocol:** Model Context Protocol (MCP / Stdio Transport)
* **Graph Analytics:** NetworkX
* **Automation:** PyGithub / GitHub REST API
* **UI/UX:** Rich Console Engine
* **Containerization:** Docker Compose

---

## 🚀 Quick Start

### 1. Prerequisites & Environment Variables
Create a `.env` file in the root directory:

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=amazon.nova-pro-v1:0

GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPOSITORY=owner/repository_name
```

### 2. Run with Docker Compose
Build and launch the agent environment in interactive mode:

```env

docker compose run --build --rm strands-agent
```


---

### 📋 Architecture Overview

```env

┌─────────────────────────┐         stdio MCP          ┌───────────────────────────┐
│                         │ ─────────────────────────> │                           │
│   Strands Agent Engine  │                            │  Custom MCP Server        │
│   (Bedrock Nova Pro)    │ <───────────────────────── │  (NetworkX + PII Engine)  │
│                         │         Tools List         │                           │
└────────────┬────────────┘                            └───────────────────────────┘
             │
             │ Approved via HITL
             ▼
┌─────────────────────────┐
│   GitHub Auto-PR Tool   │ ───> Creates Branch & Governance PR
└─────────────────────────┘
```

---

## 📸 Demo & Execution Flow

### 1. Terminal Output & Human-In-The-Loop Approval
When high-risk datasets or lineage vulnerabilities are detected, the agent triggers an interactive Human-In-The-Loop (HITL) prompt before dispatching any fixes:

```text
╭─────────────────────────────────── Final Agent Governance Decision ───────────────────────────────────╮
│ <thinking> High-risk datasets identified with sensitive PII fields and high centrality scores.         │
│ Automated remediation is ready for deployment. </thinking>                                            │
│                                                                                                       │
│ The governance audit on the enterprise data pipeline is complete.                                     │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─────────────────────────────── Human-In-The-Loop Intervention Required ───────────────────────────────╮
│ 🚨 GOVERNANCE AUDIT COMPLETE                                                                          │
│ High-priority or sensitive data lineage fields evaluated.                                             │
│ Automated remediation is ready for deployment.                                                        │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────╯

Do you authorize automated remediation and GitHub PR creation? [y/n] (n): y

✅ Operator APPROVED remediation. Dispatching GitHub PR...
🚀 SUCCESS: Created GitHub PR: [https://github.com/evaaliya/albugent_v2.0/pull/3](https://github.com/evaaliya/albugent_v2.0/pull/3)
```

### 2. Automated Remediation Pull Request
Upon operator approval, Albugent 2.0 automatically creates a dedicated git branch and submits a comprehensive Pull Request containing the governance audit report:

![image](https://github.com/evaaliya/albugent_v2.0/blob/main/docs/images/Automated%20PR%20showcase.png)

### 📄 License
This project is licensed under the Apache-2.0 License - see the LICENSE file for details.
