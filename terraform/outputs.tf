output "cluster_name" {
  description = "k3d cluster name"
  value       = var.cluster_name
}

output "api_url" {
  description = "DocuMind API (via Ingress)"
  value       = "http://documind.local:8080"
}

output "swagger_url" {
  description = "Swagger UI"
  value       = "http://documind.local:8080/docs"
}

output "grafana_url" {
  description = "Grafana dashboard (port-forward required)"
  value       = "kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3000:80"
}

output "prometheus_url" {
  description = "Prometheus (port-forward required)"
  value       = "kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090"
}

output "namespace" {
  description = "Application namespace"
  value       = var.namespace
}
