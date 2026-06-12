variable "app_name" {
  description = "Application name"
  type        = string
}

variable "api_key" {
  description = "Hostinger API key"
  type        = string
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
