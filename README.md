# DocuMind — Enterprise AI Document Intelligence Platform

> **End-to-End MLOps & DevOps Reference — MacBook Pro M5 / 16 GB**
> LangChain · FastAPI · Docker · Kubernetes · Terraform · Prometheus · Grafana

[![CI](https://github.com/saisarantottempudi/documind/actions/workflows/ci.yml/badge.svg)](https://github.com/saisarantottempudi/documind/actions/workflows/ci.yml)

---

## What Is This?

DocuMind is a production-grade **RAG (Retrieval-Augmented Generation)** platform — the kind large enterprises build internally so employees can query thousands of documents (policies, manuals, reports) in plain English and get precise, source-cited answers.

It is also a **complete DevOps reference project** built from the ground up in 10 committed steps, covering every layer of the modern infrastructure stack — designed to run fully offline on a MacBook Pro M5 with 16 GB RAM.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                │
│               Browser  /  curl  /  Postman  /  CI smoke test         │
└─────────────────────────────┬────────────────────────────────────────┘
                              │ HTTP
┌─────────────────────────────▼────────────────────────────────────────┐
│              NGINX INGRESS CONTROLLER (k8s / k3d)                    │
│                     documind.local:8080                              │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
┌─────────────────────────────▼────────────────────────────────────────┐
│            FastAPI Application  (2–8 pods, HPA-managed)              │
│                                                                      │
│  POST /documents/upload ──► Chunker ──► Embedder ──► ChromaDB        │
│  POST /query            ──► Retriever ──► CoT LLM ──► JSON response  │
│  GET  /health  /liveness  /readiness  /metrics                       │
└──────┬─────────────────────────────────────────────────┬─────────────┘
       │                                                 │
┌──────▼──────┐   ┌──────────────┐   ┌──────────────────▼──────┐
│  ChromaDB   │   │    Redis     │   │    Ollama (llama3.2:3b)  │
│ Vector Store│   │  LRU Cache   │   │  Apple Silicon GPU/CPU   │
└─────────────┘   └──────────────┘   └─────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     MONITORING STACK                                │
│  Prometheus ──► Alert rules ──► Alertmanager                        │
│  Grafana (10-panel dashboard: req/s, error%, p99, HPA replicas…)    │
└─────────────────────────────────────────────────────────────────────┘
```

### RAG + Chain-of-Thought Pipeline

```
  Document upload (PDF / TXT)
        │
        ▼
  Text extraction (pypdf / plain text)
        │
        ▼
  RecursiveCharacterTextSplitter  chunk_size=512 overlap=64
        │
        ▼
  Sentence-Transformers  all-MiniLM-L6-v2  (runs on Apple MPS)
        │
        ▼
  ChromaDB vector store  (persistent volume)
        │
  Query ──► similarity_search top-k=5
                │
                ▼
  Chain-of-Thought Prompt:
    1. UNDERSTAND the question
    2. SCAN retrieved passages
    3. REASON step by step
    4. ANSWER concisely
    5. CITE sources
                │
                ▼
  Ollama  llama3.2:3b  (local, no API key, ~2 GB)
                │
                ▼
  JSON  { answer, sources[], reasoning_steps[], cached }
```

---

## The 10-Step DevOps Journey

| # | What Was Built | Files |
|---|---------------|-------|
| 1 | GitHub repo, directory skeleton, architecture README | `README.md`, `.gitignore`, `.env.example` |
| 2 | FastAPI + LangChain RAG application (full ML core) | `app/` |
| 3 | pytest unit + integration test suite | `tests/` |
| 4 | Multi-stage Dockerfile + Docker Compose full stack | `docker/`, `docker-compose.yml` |
| 5 | GitHub Actions CI: lint→test→build→push GHCR→Trivy | `.github/workflows/ci.yml` |
| 6 | k3d cluster config + raw Kubernetes manifests | `k8s/` |
| 7 | Helm chart (parameterised, Bitnami Redis subchart) | `helm/documind/` |
| 8 | Terraform IaC: cluster + nginx + prometheus + app | `terraform/` |
| 9 | Prometheus scrape rules + alert rules + Grafana dashboard | `monitoring/` |
| 10 | NetworkPolicy, PDB, ResourceQuota, LimitRange, scripts | `k8s/network-policy.yaml`, `k8s/pdb.yaml`, `scripts/` |

---

## Quick Start

### 0 — Prerequisites (one-time)

```bash
# Install tools (macOS Apple Silicon)
brew tap hashicorp/tap
brew install hashicorp/tap/terraform helm k3d
brew install --cask ollama

# Pull the LLM (~2 GB, runs fully local on M5)
ollama pull llama3.2:3b
```

### 1 — Clone and bootstrap

```bash
git clone https://github.com/saisarantottempudi/documind
cd documind
bash scripts/setup.sh        # creates .venv, runs tests, confirms deps
```

### 2 — Local development (Docker Compose)

```bash
docker compose up -d

# Upload a document
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@/path/to/your.pdf"

# Query it
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key findings in this document?"}'

# Swagger UI
open http://localhost:8000/docs

# Grafana dashboard
open http://localhost:3000    # admin / admin
```

### 3 — Deploy to Kubernetes (k3d, runs locally)

**Option A — Terraform (recommended, full IaC)**

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars  # edit if needed
terraform init
terraform apply       # ~5 min first run (pulls images)
terraform output      # prints URLs and port-forward commands
```

**Option B — Helm direct**

```bash
k3d cluster create --config k8s/k3d-config.yaml

# Install nginx ingress
helm install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Deploy app
bash scripts/deploy.sh latest

# Add to /etc/hosts (once)
echo "127.0.0.1 documind.local" | sudo tee -a /etc/hosts
open http://documind.local:8080/docs
```

**Option C — Raw kubectl**

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/network-policy.yaml
kubectl apply -f k8s/pdb.yaml
kubectl apply -f k8s/resource-quota.yaml
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/documents/upload` | Upload PDF or TXT (multipart) |
| `GET` | `/documents/` | List all indexed documents |
| `DELETE` | `/documents/{doc_id}` | Remove a document from vector store |
| `POST` | `/query` | Ask a question (CoT RAG) |
| `GET` | `/health` | All dependency status |
| `GET` | `/liveness` | K8s liveness probe |
| `GET` | `/readiness` | K8s readiness probe |
| `GET` | `/metrics` | Prometheus scrape endpoint |

**Query request body:**
```json
{
  "question": "What is the leave policy for remote employees?",
  "top_k": 5
}
```

**Query response:**
```json
{
  "question": "...",
  "answer": "Employees get 20 days annual leave...",
  "sources": [
    { "doc_id": "...", "filename": "hr-policy.pdf", "chunk_index": 3, "content": "...", "score": 0.91 }
  ],
  "reasoning_steps": ["1. UNDERSTAND: ...", "2. SCAN: ...", "3. REASON: ..."],
  "cached": false
}
```

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| ML Orchestration | LangChain | 0.3 |
| LLM | Ollama + llama3.2:3b | local |
| Embeddings | sentence-transformers all-MiniLM-L6-v2 | 3.3 |
| Vector Store | ChromaDB | 0.5 |
| Cache | Redis | 7 |
| API | FastAPI + Uvicorn | 0.115 |
| Containerisation | Docker (multi-stage) | 28 |
| Local Kubernetes | k3d (k3s) | 5.8 / k3s 1.33 |
| Package manager | Helm | 4.1 |
| IaC | Terraform | 1.15 |
| CI/CD | GitHub Actions + GHCR | — |
| Monitoring | Prometheus + Grafana | latest |
| Security scan | Trivy | — |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Model to use |
| `CHROMA_HOST` | `chromadb` | ChromaDB hostname |
| `REDIS_URL` | `redis://redis:6379` | Redis connection |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `CHUNK_SIZE` | `512` | Text chunk size (tokens) |
| `CHUNK_OVERLAP` | `64` | Chunk overlap |
| `TOP_K` | `5` | Retrieval top-k |
| `CACHE_TTL_SECONDS` | `300` | Redis TTL per query |
| `LOG_LEVEL` | `info` | Uvicorn / structlog level |
| `APP_ENV` | `development` | `development` = pretty logs, `production` = JSON |

---

## Production Hardening (Step 10)

| Control | What It Does |
|---------|-------------|
| `NetworkPolicy` | Zero-trust: deny all ingress by default, only allow exact pod-to-pod traffic |
| `PodDisruptionBudget` | Keeps ≥2 API pods alive during node drains and upgrades |
| `ResourceQuota` | Namespace-level CPU/memory/pod caps |
| `LimitRange` | Default requests/limits for any pod that omits them |
| Non-root container | `runAsUser: 1000`, `runAsNonRoot: true` |
| Rolling update | `maxUnavailable: 1`, `maxSurge: 1` |
| HPA | 2–8 replicas, scale on CPU 70% + memory 80% |
| Secrets | K8s Secret for sensitive values (use Sealed Secrets in real prod) |

---

## Monitoring Endpoints

| URL | What |
|-----|------|
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/metrics` | Prometheus metrics |
| `http://localhost:9090` | Prometheus (Docker Compose) |
| `http://localhost:3000` | Grafana — admin/admin (Docker Compose) |

**K8s port-forwards:**
```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana   3000:80
```

---

## Running Tests

```bash
# Unit tests (no containers needed)
pytest tests/unit/ -v

# Integration tests (services mocked)
pytest tests/integration/ -v

# Full suite with coverage
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Directory Structure

```
documind/
├── app/                         ← FastAPI application
│   ├── api/routes/              ← documents.py, query.py, health.py
│   ├── core/                   ← config.py, logging.py
│   ├── models/schemas.py       ← Pydantic v2 models
│   └── services/               ← embedder, vectorstore, cache, llm, rag
├── tests/
│   ├── unit/                   ← config, schemas, llm, cache, rag
│   └── integration/            ← full API via TestClient
├── docker/
│   ├── Dockerfile              ← multi-stage prod
│   └── Dockerfile.dev          ← hot-reload dev
├── docker-compose.yml          ← full local stack
├── docker-compose.prod.yml     ← prod overrides
├── k8s/                        ← raw Kubernetes manifests
│   ├── namespace, configmap, secret, pvc
│   ├── deployment, service, ingress, hpa
│   ├── network-policy, pdb, resource-quota
│   └── k3d-config.yaml
├── helm/documind/              ← Helm chart
│   ├── Chart.yaml, values.yaml
│   └── templates/              ← all K8s resources as templates
├── terraform/                  ← IaC
│   ├── main.tf                 ← k3d + nginx + prometheus + app
│   ├── variables.tf, outputs.tf, providers.tf, versions.tf
│   └── terraform.tfvars.example
├── monitoring/
│   ├── prometheus/             ← scrape config + alert rules
│   └── grafana/                ← provisioning + 10-panel dashboard
├── scripts/
│   ├── setup.sh               ← one-shot local setup
│   └── deploy.sh              ← helm upgrade wrapper
└── .github/workflows/
    ├── ci.yml                  ← lint, test, build, push, trivy
    ├── cd.yml                  ← helm deploy on main
    └── pr-checks.yml           ← size label + dep review
```

---

## License

MIT
