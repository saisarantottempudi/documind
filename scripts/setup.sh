#!/usr/bin/env bash
# setup.sh — One-shot local environment setup for DocuMind
# Run this once after cloning the repo.
set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

info()    { echo -e "${CYAN}[setup]${NC} $*"; }
success() { echo -e "${GREEN}[ok]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[warn]${NC}  $*"; }

info "Checking prerequisites..."

for cmd in docker python3 git; do
  command -v "$cmd" &>/dev/null && success "$cmd found" || { echo "ERROR: $cmd not installed"; exit 1; }
done

for cmd in kubectl helm k3d terraform; do
  command -v "$cmd" &>/dev/null && success "$cmd found" || warn "$cmd not found — install via brew"
done

info "Checking Ollama..."
if command -v ollama &>/dev/null || [ -d "/Applications/Ollama.app" ]; then
  success "Ollama found"
  info "Pulling llama3.2:3b (this will take ~2 GB on first run)..."
  ollama pull llama3.2:3b && success "Model ready" || warn "Could not pull model — start Ollama app first"
else
  warn "Ollama not found — install from https://ollama.com"
fi

info "Setting up Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -e ".[dev]" -q
success "Python env ready (.venv)"

info "Copying .env..."
[ -f .env ] || cp .env.example .env && success ".env created"

info "Running tests to verify setup..."
pytest tests/ -q --no-header 2>&1 | tail -5
success "Setup complete!"
echo ""
echo "  Start local stack:   docker compose up -d"
echo "  API docs:            http://localhost:8000/docs"
echo "  Grafana:             http://localhost:3000  (admin/admin)"
echo "  Deploy to k8s:       cd terraform && terraform init && terraform apply"
