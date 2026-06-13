variable "app_name" {
  description = "Application name"
  type        = string
}

variable "vps_ip" {
  description = "Public IP of the VPS (created manually in hPanel; see setup guide)"
  type        = string
}

variable "manage_vps" {
  description = "If true, attempt to provision the VPS via the Hostinger API (off by default)"
  type        = bool
  default     = false
}

variable "api_key" {
  description = "Hostinger API key (only needed when manage_vps = true)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "vps_plan" {
  description = "VPS plan name"
  type        = string
}

variable "region" {
  description = "Datacenter region"
  type        = string
}
