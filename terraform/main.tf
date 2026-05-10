# ── DocuMind — Terraform IaC ────────────────────────────────────────────────────
# Provisions a local k3d cluster and deploys the full stack via Helm.
#
# Usage:
#   terraform init
#   terraform plan
#   terraform apply
#
# Tear down:
#   terraform destroy

# ── 1. k3d cluster (provisioned via null_resource + local-exec) ─────────────────
resource "null_resource" "k3d_cluster" {
  triggers = {
    cluster_name = var.cluster_name
    servers      = var.k3d_servers
    agents       = var.k3d_agents
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -e
      # Destroy existing cluster with same name if it exists
      k3d cluster list | grep -q "^${var.cluster_name}" && \
        k3d cluster delete ${var.cluster_name} || true

      k3d cluster create ${var.cluster_name} \
        --servers ${var.k3d_servers} \
        --agents  ${var.k3d_agents} \
        --port    "8080:80@loadbalancer" \
        --port    "8443:443@loadbalancer" \
        --k3s-arg "--disable=traefik@server:*" \
        --wait

      # Update local kubeconfig
      k3d kubeconfig merge ${var.cluster_name} --kubeconfig-switch-context
    EOT
    interpreter = ["/bin/bash", "-c"]
  }

  provisioner "local-exec" {
    when    = destroy
    command = "k3d cluster delete ${self.triggers.cluster_name} || true"
    interpreter = ["/bin/bash", "-c"]
  }
}

# ── 2. Wait for cluster API to be ready ─────────────────────────────────────────
resource "null_resource" "wait_for_cluster" {
  depends_on = [null_resource.k3d_cluster]

  provisioner "local-exec" {
    command     = "kubectl wait --for=condition=Ready nodes --all --timeout=120s"
    interpreter = ["/bin/bash", "-c"]
  }
}

# ── 3. Nginx Ingress Controller ──────────────────────────────────────────────────
resource "helm_release" "nginx_ingress" {
  depends_on = [null_resource.wait_for_cluster]

  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = "4.11.0"
  namespace        = "ingress-nginx"
  create_namespace = true

  set {
    name  = "controller.service.type"
    value = "LoadBalancer"
  }

  wait    = true
  timeout = 300
}

# ── 4. kube-prometheus-stack (Prometheus + Grafana + Alertmanager) ───────────────
resource "helm_release" "prometheus_stack" {
  depends_on = [null_resource.wait_for_cluster]

  name             = "kube-prometheus-stack"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "67.0.0"
  namespace        = "monitoring"
  create_namespace = true

  set {
    name  = "prometheus.prometheusSpec.retention"
    value = var.prometheus_retention
  }
  set {
    name  = "grafana.adminPassword"
    value = var.grafana_admin_password
  }
  set {
    name  = "grafana.service.type"
    value = "ClusterIP"
  }
  set {
    name  = "prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  wait    = true
  timeout = 600
}

# ── 5. DocuMind application ──────────────────────────────────────────────────────
resource "helm_release" "documind" {
  depends_on = [
    helm_release.nginx_ingress,
    helm_release.prometheus_stack,
  ]

  name             = "documind"
  chart            = "${path.module}/../helm/documind"
  namespace        = var.namespace
  create_namespace = true

  set {
    name  = "api.image.tag"
    value = var.api_image_tag
  }
  set {
    name  = "api.replicaCount"
    value = var.api_replicas
  }
  set {
    name  = "ollama.model"
    value = var.ollama_model
  }
  set {
    name  = "monitoring.serviceMonitor.enabled"
    value = "true"
  }

  wait    = true
  timeout = 600
}
