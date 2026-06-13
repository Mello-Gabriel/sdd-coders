# Hostinger has no official, stable Terraform provider. The supported path is to
# create the VPS by hand in hPanel (see docs/guides/setup.md) and pass its IP in
# via var.vps_ip. The optional null_resource below can call the Hostinger API for
# fully-automated provisioning, but it is OFF by default (var.manage_vps = false)
# because the API surface changes and the call is not idempotent.

resource "null_resource" "vps" {
  count = var.manage_vps ? 1 : 0

  triggers = {
    app_name = var.app_name
    vps_plan = var.vps_plan
    region   = var.region
  }

  provisioner "local-exec" {
    # The API key is passed through the environment, never interpolated into the
    # command line (which would leak it into process listings and TF logs).
    environment = {
      HOSTINGER_API_KEY = var.api_key
    }
    command = <<-EOT
      curl -fsS -X POST "https://api.hostinger.com/v1/vps" \
        -H "Authorization: Bearer $HOSTINGER_API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"name":"${var.app_name}","plan":"${var.vps_plan}","region":"${var.region}"}'
    EOT
  }
}
