provider "cloudflare" {
  api_token = var.api_token
}

# A record for the frontend (apex)
resource "cloudflare_record" "frontend" {
  zone_id = var.zone_id
  name    = "@"
  type    = "A"
  value   = var.vps_ip
  proxied = true
}

# A record for the API subdomain
resource "cloudflare_record" "backend" {
  zone_id = var.zone_id
  name    = "api"
  type    = "A"
  value   = var.vps_ip
  proxied = true
}

# WAF rule: block requests without a valid Turnstile token on auth endpoints
resource "cloudflare_ruleset" "turnstile_gate" {
  zone_id     = var.zone_id
  name        = "${var.app_name}-turnstile"
  description = "Require Turnstile validation on auth routes"
  kind        = "zone"
  phase       = "http_request_firewall_custom"

  rules {
    action      = "challenge"
    description = "Turnstile challenge on auth endpoints"
    expression  = "(http.request.uri.path contains \"/auth/register\" or http.request.uri.path contains \"/auth/request-password-reset\")"
    enabled     = true
  }
}
