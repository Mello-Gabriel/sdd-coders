# Hostinger does not yet have a stable Terraform provider.
# VPS provisioning is done via the Hostinger API using null_resource + local-exec.
# Replace with the official provider when available.

resource "null_resource" "vps" {
  triggers = {
    app_name = var.app_name
    vps_plan = var.vps_plan
    region   = var.region
  }

  provisioner "local-exec" {
    command = <<-EOT
      curl -s -X POST "https://api.hostinger.com/v1/vps" \
        -H "Authorization: Bearer ${var.api_key}" \
        -H "Content-Type: application/json" \
        -d '{"name":"${var.app_name}","plan":"${var.vps_plan}","region":"${var.region}"}' \
        | tee /tmp/hostinger_vps.json
    EOT
  }
}

# VPS IP is populated after provisioning. In a real workflow, read it from
# the API response or a data source after the resource is created.
