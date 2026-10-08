# SentinelRAG

Enterprise RAG with RBAC (Role-Based Access Control) for Stratos Enterprises.

## Phase 1 Complete
Project scaffolding, environment setup, logging, and FastAPI foundation have been configured.

## Setup Instructions

1. **Create Virtual Environment:**
   ``bash
   cd backend
   python -m venv venv
   source venv/Scripts/activate  # Windows
   ``

2. **Install Requirements:**
   ``bash
   pip install -r requirements.txt
   ``

3. **Environment Variables:**
   Copy .env.example to .env and populate it with your actual keys.
   ``bash
   cp .env.example .env
   ``

4. **Run the Server:**
   ``bash
   uvicorn app.main:app --reload
   ``
