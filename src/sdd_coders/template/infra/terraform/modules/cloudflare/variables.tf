variable "zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "domain" {
  description = "Root domain"
  type        = string
}

variable "app_name" {
  description = "Application name"
  type        = string
}

variable "vps_ip" {
  description = "Public IP of the VPS to point DNS records at"
  type        = string
}

variable "api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}
