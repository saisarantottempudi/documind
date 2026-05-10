# DocuMind — Enterprise AI Document Intelligence Platform

> **End-to-End MLOps & DevOps Reference Implementation**
> LangChain · FastAPI · Docker · Kubernetes · Terraform · Prometheus · Grafana

---

## What This Is

DocuMind is a production-grade **RAG (Retrieval-Augmented Generation)** system — the kind MNCs like Deloitte, HSBC, and Accenture build internally so employees can query thousands of documents (policies, manuals, reports) using plain English.

It is **also** a complete DevOps reference project covering every layer of the modern infrastructure stack, designed to run fully on a MacBook Pro M5 / 16 GB.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│              Browser  /  curl  /  Postman                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────────┐
│                    NGINX INGRESS (k8s)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                  FastAPI Application (3 replicas)               │
│                                                                 │
│  POST /documents/upload  ──►  Chunker ──► Embedder ──► ChromaDB │
│  POST /query             ──►  Retriever ──► LLM ──► Response    │
│  GET  /health            ──►  liveness / readiness              │
│  GET  /metrics           ──►  Prometheus scrape endpoint        │
└──────┬────────────────────────────────────────────────────────┬─┘
       │                                                        │
┌──────▼──────┐   ┌──────────────┐   ┌────────────────────┐   │
│   ChromaDB  │   │    Redis     │   │   Ollama (LLM)     │   │
│ Vector Store│   │    Cache     │   │  llama3.2:3b local │   │
└─────────────┘   └──────────────┘   └────────────────────┘   │
                                                               │
┌──────────────────────────────────────────────────────────────▼─┐
│              MONITORING STACK                                   │
│   Prometheus ──► Grafana dashboards ──► Alertmanager           │
└────────────────────────────────────────────────────────────────┘
```

### RAG Pipeline (Chain-of-Thought)

```
Document Upload
      │
      ▼
  PDF/TXT Parser (pypdf / python-docx)
      │
      ▼
  Recursive Text Splitter (chunk_size=512, overlap=64)
      │
      ▼
  Sentence Transformer Embeddings (all-MiniLM-L6-v2, local, no API key)
      │
      ▼
  ChromaDB Vector Store (persistent, Docker volume)
      │
Query ──► Similarity Search (top-k=5)
               │
               ▼
      Chain-of-Thought Prompt:
        "Think step by step. First identify what the question is asking.
         Then scan the retrieved context for relevant facts.
         Then synthesise a precise answer citing the source chunks."
               │
               ▼
      Ollama LLM (llama3.2:3b — runs on Apple Silicon)
               │
               ▼
      Structured JSON Response + source citations
```

---

## Project Steps (DevOps Journey)

| Step | What Is Built | Branch / Tag |
|------|--------------|--------------|
| 1 | Project skeleton, architecture, README | `step/01-bootstrap` |
| 2 | FastAPI + LangChain RAG application | `step/02-ml-app` |
| 3 | pytest unit + integration tests | `step/03-tests` |
| 4 | Multi-stage Dockerfile + Docker Compose | `step/04-docker` |
| 5 | GitHub Actions CI (lint → test → build → push GHCR → Trivy) | `step/05-ci` |
| 6 | k3d cluster + Kubernetes manifests | `step/06-kubernetes` |
| 7 | Helm chart | `step/07-helm` |
| 8 | Terraform IaC (cluster + Helm releases) | `step/08-terraform` |
| 9 | Prometheus + Grafana monitoring | `step/09-monitoring` |
| 10 | Production hardening (NetworkPolicy, PDB, limits) | `step/10-hardening` |

---

## Quick Start

### Prerequisites

```bash
# macOS (Apple Silicon)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform helm k3d
brew install --cask ollama

# Pull the LLM (one-time, ~2 GB)
ollama pull llama3.2:3b
```

### Local Development (Docker Compose)

```bash
git clone https://github.com/saisarantottempudi/documind
cd documind

# Start full stack (API + ChromaDB + Redis + Ollama)
docker compose up -d

# Upload a document
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@/path/to/your.pdf"

# Query it
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key findings?"}'
```

### Kubernetes (k3d — runs locally)

```bash
# Provision cluster via Terraform
cd terraform
terraform init && terraform apply

# Or manually
k3d cluster create documind --config k3d-config.yaml

# Deploy via Helm
helm install documind ./helm/documind -f helm/documind/values.yaml

# Watch pods come up
kubectl get pods -n documind -w
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| ML Orchestration | LangChain 0.3 |
| LLM | Ollama + llama3.2:3b (local, Apple Silicon) |
| Embeddings | sentence-transformers / all-MiniLM-L6-v2 |
| Vector Store | ChromaDB |
| Cache | Redis 7 |
| API | FastAPI + Uvicorn |
| Containerisation | Docker (multi-stage, distroless) |
| Orchestration | Kubernetes 1.33 via k3d |
| Package Manager | Helm 4 |
| IaC | Terraform 1.15 |
| CI/CD | GitHub Actions + GHCR |
| Monitoring | Prometheus + Grafana + Alertmanager |
| Security Scan | Trivy |

---

## Directory Structure

```
documind/
├── app/                    ← FastAPI application
│   ├── api/routes/         ← HTTP route handlers
│   ├── core/               ← Config, logging
│   ├── services/           ← RAG pipeline, embedder, vector store, LLM
│   └── models/             ← Pydantic schemas
├── tests/                  ← pytest (unit + integration)
├── docker/                 ← Dockerfiles
├── docker-compose.yml      ← Full local stack
├── k8s/                    ← Raw Kubernetes manifests
├── helm/documind/          ← Helm chart
├── terraform/              ← IaC for cluster + releases
├── monitoring/             ← Prometheus rules + Grafana dashboards
├── scripts/                ← Helper shell scripts
└── .github/workflows/      ← CI/CD pipelines
```

---

## Monitoring Endpoints

| URL | What |
|-----|------|
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/metrics` | Prometheus metrics |
| `http://localhost:9090` | Prometheus |
| `http://localhost:3000` | Grafana (admin/admin) |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model name |
| `CHROMA_HOST` | `chromadb` | ChromaDB host |
| `REDIS_URL` | `redis://redis:6379` | Redis connection |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `LOG_LEVEL` | `info` | Uvicorn log level |

---

## License

MIT
