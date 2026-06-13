variable "app_name" {
  description = "Application name (used as prefix for resources)"
  type        = string
}

variable "domain" {
  description = "Root domain for the application (e.g. example.com)"
  type        = string
}

# --- VPS / Hostinger ---

variable "vps_ip" {
  description = "Public IP of the VPS (create it manually in hPanel; see setup guide)"
  type        = string
}

variable "manage_vps" {
  description = "Provision the VPS via the Hostinger API instead of using a manual one"
  type        = bool
  default     = false
}

variable "hostinger_api_key" {
  description = "Hostinger API key (only needed when manage_vps = true)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "hostinger_vps_plan" {
  description = "Hostinger VPS plan (e.g. KVM 2)"
  type        = string
  default     = "KVM 2"
}

variable "hostinger_region" {
  description = "Hostinger datacenter region (e.g. eu-west-1)"
  type        = string
  default     = "eu-west-1"
}

# --- Cloudflare ---

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone:Edit and DNS:Edit permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID for the root domain"
  type        = string
}

variable "turnstile_secret_key" {
  description = "Cloudflare Turnstile secret key"
  type        = string
  sensitive   = true
}

# --- Coolify ---

variable "coolify_url" {
  description = "URL of the Coolify instance (e.g. https://coolify.example.com)"
  type        = string
}

variable "coolify_token" {
  description = "Coolify API token"
  type        = string
  sensitive   = true
}
