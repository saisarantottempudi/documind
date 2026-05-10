# Providers read from the default kubeconfig that k3d updates.
# After `terraform apply`, kubeconfig points to the new cluster.

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "k3d-documind"
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "k3d-documind"
  }
}
