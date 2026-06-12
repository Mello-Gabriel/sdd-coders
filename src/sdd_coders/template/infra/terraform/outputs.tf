output "vps_ip" {
  description = "Public IP of the VPS"
  value       = module.hostinger.vps_ip
}

output "backend_url" {
  description = "Public URL of the backend API"
  value       = module.cloudflare.backend_url
}

output "frontend_url" {
  description = "Public URL of the frontend"
  value       = module.cloudflare.frontend_url
}
