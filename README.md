# 🛡️ Stratos Enterprise (SentinelRAG)

> **Enterprise-Grade, Security-Hardened Agentic RAG Platform**  
> Powered by **FastAPI**, **Next.js 16**, **Qdrant Vector DB**, and **Groq LPU Inference**.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.2-black?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Qdrant](https://img.shields.io/badge/Qdrant-Cloud_Vector_DB-DC382D?style=flat-square&logo=qdrant&logoColor=white)](https://qdrant.tech)
[![Groq](https://img.shields.io/badge/Groq-Ultra_Fast_LLM-F55036?style=flat-square)](https://groq.com)
[![License](https://img.shields.io/badge/License-Proprietary-blue.svg?style=flat-square)](#)

---

## 📌 Executive Overview

**Stratos Enterprise** is an internal corporate AI assistant designed for high-security enterprise environments. Unlike standard chatbot wrappers, Stratos features an end-to-end **Sentinel architecture** combining **Hybrid RAG** (Dense Vector + BM25 Lexical search merged via Reciprocal Rank Fusion), strict **Role-Based Access Control (RBAC)**, multi-layered **input/output guardrails**, and **autonomous agentic function calling**.

---

## 🚀 Key Features & Capabilities

### 1. 🔍 Hybrid RAG & Intelligent Routing
* **Dense + Sparse Search:** Integrates **Qdrant Cloud** semantic embeddings (`BAAI/bge-small-en-v1.5`) with lexical **BM25** ranking, unified through **Reciprocal Rank Fusion (RRF)**.
* **Intent Routing:** Automatically classifies queries into `personal_record_lookup`, `policy_or_general_info`, `aggregate_or_report`, `action_request`, or `chit_chat` to apply optimal retrieval parameters.
* **Citation Attribution:** Responses cite specific document sources, department origin, and relevance confidence.

### 2. 🔐 Multi-Tier RBAC & Strict Data Isolation
* **4-Tier Clearance Hierarchy:** `Public (0)` < `Internal (1)` < `Confidential (2)` < `Restricted (3)`.
* **Zero Data Leakage:** Security filters are injected directly into vector search queries before retrieval. Employees cannot physically query or retrieve documents exceeding their clearance.
* **Ownership & Department Filtering:** Personal documents (compensation, salary slips, appraisals) are locked to self-access or authorized direct managers only.

### 3. 🤖 Autonomous Agentic Workflows
The bot doesn't just answer questions; it executes verified enterprise actions:
* **Leave Management:** Inquire about remaining balances, submit leave requests with date validation, and allow managers to approve/reject requests.
* **Department Reporting:** Managers can synthesize real-time departmental budget and performance summaries.
* **Permission Gated:** Every tool call is evaluated against a dynamic permissions gate before execution.

### 4. 🛡️ Enterprise Guardrails & Anti-Hallucination
* **Input Defense:** Regex and LLM classifiers detect and block prompt injection, DAN mode, and system prompt extraction attacks.
* **PII Redaction:** Automatic detection and masking of sensitive identifiers (PAN cards, Aadhaar, account numbers).
* **Citation Grounding & Refusal:** Evaluates generated answers against source context. If the requested information is absent from internal documents, the assistant cleanly refuses rather than hallucinating figures.

### 5. ✨ Modern Conversational Frontend
* **Next.js 16 (React 19) UI:** Sleek corporate interface with fluid animations using **Motion** and **Tailwind CSS**.
* **Contextual Shimmer States:** Dynamic animated progress badges indicate real-time backend thinking phases (*"Scanning HR policies..."*, *"Retrieving salary breakdown..."*).
* **Role Switcher:** Instant role-switching simulation between Employee, Manager, and Admin personas.

---

## 🏗️ System Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │          Next.js 16 Web Interface            │
                  │ (Role Switcher, Shimmer States, Citations)  │
                  └──────────────────────┬───────────────────────┘
                                         │ HTTPS / JWT Auth
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             FastAPI Backend API              │
                  │  - Authentication & JWT Token Validation     │
                  │  - Input Guardrails (Jailbreak / PII Checks) │
                  └──────────────┬───────────────────────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │                               │
        [Action Request]                 [Information Query]
                 │                               │
                 ▼                               ▼
  ┌─────────────────────────────┐  ┌─────────────────────────────┐
  │     Agent Orchestrator      │  │        Hybrid RAG           │
  │  - Tool Extractor (Groq)    │  │  - Qdrant Cloud (Dense)     │
  │  - Permission Gating        │  │  - BM25 (Sparse Lexical)    │
  │  - Actions (Leave, Reports) │  │  - Reciprocal Rank Fusion   │
  └──────────────┬──────────────┘  └─────────────┬───────────────┘
                 │                               │
                 └───────────────┬───────────────┘
                                 │
                                 ▼
                  ┌──────────────────────────────┐
                  │   Output Guardrails Layer    │
                  │  - NLI Grounding Check       │
                  │  - RBAC Leak Prevention      │
                  │  - PII Masking               │
                  └──────────────┬───────────────┘
                                 │
                                 ▼
                     Verified Enterprise Response
```

---

## 📊 Benchmark Verification

The SentinelRAG architecture was rigorously benchmarked across 1,927 vectorized documents and synthetic red-team evaluation suites:

| Benchmark Dimension | Measured Score | Evaluation Standard |
| :--- | :--- | :--- |
| **Faithfulness** | **89.2%** | Validated grounded claims |
| **Answer Relevancy** | **93.0%** | Query intent alignment |
| **Context Precision** | **86.7%** | Top-k ranked relevance |
| **Context Recall** | **86.2%** | Information retrieval coverage |
| **RBAC Security Integrity** | **100.0%** | Zero leaks across 500 test queries |
| **Adversarial Red-Team Success** | **100.0%** | 0 jailbreak bypasses / 8 attack vectors |

---

## 🛠️ Tech Stack

| Component | Technologies |
| :--- | :--- |
| **Backend** | Python 3.11, FastAPI, Pydantic, Uvicorn, PyJWT |
| **LLM & Inference** | Groq LPU API (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`) |
| **Embeddings** | HuggingFace `BAAI/bge-small-en-v1.5` (384-dim) |
| **Vector Database** | Qdrant Cloud (Managed Cluster, AWS us-east-2) |
| **Lexical Search** | Rank-BM25 |
| **Frontend** | Next.js 16 (Turbopack), React 19, TypeScript, Tailwind CSS, Motion |
| **Deployment** | Docker, Render (Backend API), Vercel (Frontend UI) |

---

## 📂 Project Structure

```
Stratos Enterprise/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Auth, Chat, User, Admin endpoints
│   │   ├── agents/              # Tool definitions & permission gates
│   │   ├── config/              # App settings & Pydantic models
│   │   ├── guardrails/          # Input injection defense & output grounding
│   │   ├── ingestion/           # Document chunking & vector loader
│   │   ├── rbac/                # Clearance hierarchy & access filters
│   │   └── retrieval/           # Hybrid retriever (Qdrant + BM25)
│   ├── Dockerfile               # Production container image
│   └── requirements.txt         # Backend Python dependencies
├── frontend/
│   └── boomerang/               # Next.js 16 web application
│       ├── app/                 # App Router (dashboard, login, api)
│       ├── components/          # Chat interface, shimmer text, cards
│       └── lib/api-client.ts    # Typed API client
├── data/                        # Corporate handbooks, payroll, and dept records
├── render.yaml                  # Render deployment blueprint
└── .gitignore                   # Security exclusion rules (protecting .env)
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
* Python 3.11+
* Node.js 18+
* Docker Desktop *(optional for local Qdrant; Qdrant Cloud supported out-of-the-box)*

### 2. Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate          # Windows (or source venv/bin/activate on Mac/Linux)
pip install -r requirements.txt
```

Configure your `backend/.env` with your API keys:
```env
APP_ENV=development
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
GROQ_FAST_MODEL=openai/gpt-oss-20b
QDRANT_URL=https://your-cluster-url.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
```

Run the API:
```bash
uvicorn app.main:app --reload --port 8000
```
* API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Frontend Setup
```bash
cd frontend/boomerang
npm install
npm run dev
```
* Web Application: [http://localhost:3000](http://localhost:3000)

---

## 👥 Demo Personas (Test Credentials)

| Role | Employee ID | Name | Clearance Level | Department |
| :--- | :--- | :--- | :--- | :--- |
| **Employee** | `STX-E-010` | Meera Nair | Level 1 (Internal) | Engineering |
| **Manager** | `STX-M-003` | Vikram Malhotra | Level 2 (Confidential) | Engineering |
| **Admin** | `STX-A-001` | Rajesh Sharma | Level 3 (Restricted) | HR / Admin |

---

## 📄 License
Proprietary & Confidential — Stratos Enterprises. All rights reserved.
