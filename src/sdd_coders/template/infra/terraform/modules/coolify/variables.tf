variable "coolify_url" {
  description = "Coolify instance URL"
  type        = string
}

variable "coolify_token" {
  description = "Coolify API token"
  type        = string
  sensitive   = true
}

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "domain" {
  description = "Root domain"
  type        = string
}
