# Multi-Agent AI Research & Decision System - Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

The core orchestration engine and REST/SSE API for the **Multi-Agent AI Research & Decision System**. Built using clean architecture, async FastAPI, and autonomous micro-agents supporting dual execution modes: **Live Autonomous Web Research** and **Literature & PDF Audit**.

---

## 🌟 Capabilities & Architecture

- **Dual Multi-Agent Execution Engines**:
  - 🌐 **Web Research Mode**: Multi-source live search, citation harvesting, thematic synthesis, fact-checking, and decision report generation.
  - 📄 **Literature & PDF Audit Mode**: Ingests PDF research papers or reports, extracts page-anchored text, generates deep summaries, strategic roadmaps, vector SVG architecture diagrams, and institutional audit scores.
- **Specialized Micro-Agents**:
  - 🧭 **Coordinator Agent**: Query deconstruction, hypothesis formulation, and research strategy.
  - 🔍 **Research Agent**: Live web scraping, multi-source retrieval, and citation indexing.
  - 📖 **Literature Summarizer Agent**: Hierarchical abstract, methodology breakdown, and empirical takeaways.
  - 🚀 **Projection & Roadmap Agent**: Phased project milestones, quantitative trajectories, and critical dependencies.
  - 🎨 **Visual Diagram Agent**: Generates interactive responsive vector SVG architecture diagrams and concept art prompts.
  - 🛡️ **Verification & Literature Audit Agent**: Audits methodology rigor, evidence grounding, computes audit grades (e.g., A+), and flags gaps.
  - 👤 **Human-in-the-Loop (HITL) Gate**: Configurable pause allowing human approval/feedback injection before final reports.
  - 📝 **Decision & Report Agent**: Synthesizes executive decision briefs with strategic options matrices.
- **Real-Time Telemetry**: Server-Sent Events (SSE) streaming thoughts, tool executions, and step-by-step progress to the frontend.
- **Multi-Provider Support**: Seamlessly switch between OpenAI (GPT-4o), Google Gemini (1.5 Flash/Pro), or zero-cost Mock Simulation Mode.

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.12+
- Git

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/selvamanid2004-dot/multi-ai-backend.git
cd multi-ai-backend

# Create and activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Or on macOS/Linux
# python3 -m venv venv
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your preferred settings:

```ini
# Server Settings
PORT=8000
HOST=127.0.0.1
DEBUG=false

# Provider: 'auto', 'openai', 'gemini', or 'mock'
DEFAULT_PROVIDER="auto"

# API Keys (Optional - runs in simulation mode if empty)
OPENAI_API_KEY=""
GEMINI_API_KEY=""

# Human-In-The-Loop Review Gate
REQUIRE_HUMAN_APPROVAL=true
```

### 3. Running the Server

```bash
# Start FastAPI server with live reload
python run.py
```

The API will be available at:
- **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

## 🐳 Docker Deployment

```bash
# Build Docker image
docker build -t multi-ai-backend .

# Run container
docker run -p 8000:8000 --env-file .env multi-ai-backend
```

---

## 🧪 Testing

```bash
# Run test suite with pytest
pytest
```

---

## 📄 License

MIT License.
