#!/usr/bin/env bash
# deploy.sh — Deploy or upgrade DocuMind on the local k3d cluster via Helm.
set -euo pipefail

IMAGE_TAG="${1:-latest}"
NAMESPACE="documind"
RELEASE="documind"
CHART="./helm/documind"

echo "Deploying DocuMind image tag: $IMAGE_TAG"

kubectl create namespace "$NAMESPACE" 2>/dev/null || true

helm upgrade --install "$RELEASE" "$CHART" \
  --namespace "$NAMESPACE" \
  --set api.image.tag="$IMAGE_TAG" \
  --set monitoring.serviceMonitor.enabled=true \
  --wait \
  --timeout 5m

echo "Rollout status:"
kubectl rollout status deployment/documind-api -n "$NAMESPACE" --timeout=3m

echo ""
echo "Pods:"
kubectl get pods -n "$NAMESPACE"

echo ""
echo "Access API: http://documind.local:8080/docs"
echo "  (add '127.0.0.1 documind.local' to /etc/hosts if needed)"
