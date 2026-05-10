variable "cluster_name" {
  description = "Name of the k3d cluster"
  type        = string
  default     = "documind"
}

variable "k3d_servers" {
  description = "Number of k3d server nodes"
  type        = number
  default     = 1
}

variable "k3d_agents" {
  description = "Number of k3d agent nodes"
  type        = number
  default     = 2
}

variable "namespace" {
  description = "Kubernetes namespace for the application"
  type        = string
  default     = "documind"
}

variable "api_image_tag" {
  description = "Docker image tag for the DocuMind API"
  type        = string
  default     = "latest"
}

variable "api_replicas" {
  description = "Initial replica count for the API"
  type        = number
  default     = 3
}

variable "ollama_model" {
  description = "Ollama model to pull and serve"
  type        = string
  default     = "llama3.2:3b"
}

variable "prometheus_retention" {
  description = "Prometheus TSDB retention period"
  type        = string
  default     = "15d"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = "admin"
}
