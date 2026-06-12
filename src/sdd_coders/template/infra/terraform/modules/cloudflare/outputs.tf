output "frontend_url" {
  description = "Public URL of the frontend"
  value       = "https://${var.domain}"
}

output "backend_url" {
  description = "Public URL of the backend API"
  value       = "https://api.${var.domain}"
}
