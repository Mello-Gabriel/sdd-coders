# Coolify has no official Terraform provider. Environments are created via its
# REST API. The token is passed through the environment (never interpolated into
# the command line, which would leak it into TF logs / process listings).

resource "null_resource" "coolify_dev_env" {
  triggers = {
    app_name = var.app_name
  }

  provisioner "local-exec" {
    environment = {
      COOLIFY_TOKEN = var.coolify_token
    }
    command = <<-EOT
      curl -fsS -X POST "${var.coolify_url}/api/v1/environments" \
        -H "Authorization: Bearer $COOLIFY_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name":"${var.app_name}-dev","project_uuid":"default"}'
    EOT
  }
}

resource "null_resource" "coolify_prod_env" {
  triggers = {
    app_name = var.app_name
  }

  provisioner "local-exec" {
    environment = {
      COOLIFY_TOKEN = var.coolify_token
    }
    command = <<-EOT
      curl -fsS -X POST "${var.coolify_url}/api/v1/environments" \
        -H "Authorization: Bearer $COOLIFY_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"name":"${var.app_name}-prod","project_uuid":"default"}'
    EOT
  }
}
