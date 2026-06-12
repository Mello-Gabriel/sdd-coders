# Coolify does not have an official Terraform provider.
# Environments and applications are managed via the Coolify REST API.

locals {
  coolify_headers = "-H \"Authorization: Bearer ${var.coolify_token}\" -H \"Content-Type: application/json\""
}

resource "null_resource" "coolify_dev_env" {
  triggers = {
    app_name = var.app_name
  }

  provisioner "local-exec" {
    command = <<-EOT
      curl -sf -X POST "${var.coolify_url}/api/v1/environments" \
        ${local.coolify_headers} \
        -d '{"name":"${var.app_name}-dev","project_uuid":"default"}' \
        | tee /tmp/coolify_dev_env.json
    EOT
  }
}

resource "null_resource" "coolify_prod_env" {
  triggers = {
    app_name = var.app_name
  }

  provisioner "local-exec" {
    command = <<-EOT
      curl -sf -X POST "${var.coolify_url}/api/v1/environments" \
        ${local.coolify_headers} \
        -d '{"name":"${var.app_name}-prod","project_uuid":"default"}' \
        | tee /tmp/coolify_prod_env.json
    EOT
  }
}
