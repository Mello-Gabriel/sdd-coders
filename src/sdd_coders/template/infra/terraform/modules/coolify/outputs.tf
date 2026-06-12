output "dev_environment_name" {
  description = "Name of the dev environment in Coolify"
  value       = "${var.app_name}-dev"
}

output "prod_environment_name" {
  description = "Name of the prod environment in Coolify"
  value       = "${var.app_name}-prod"
}
