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

# Edge rate limiting on auth endpoints — a network-level complement to the app's
# own rate limiter and IP-ban ladder. A managed "challenge" would break the JSON
# API and the app's own Turnstile flow, so we block instead.
resource "cloudflare_ruleset" "auth_rate_limit" {
  zone_id = var.zone_id
  name    = "${var.app_name}-auth-ratelimit"
  kind    = "zone"
  phase   = "http_ratelimit"

  rules {
    action      = "block"
    description = "Rate limit auth endpoints (per IP)"
    expression  = "(http.request.uri.path contains \"/auth/\")"
    enabled     = true

    ratelimit {
      characteristics     = ["ip.src", "cf.colo.id"]
      period              = 60
      requests_per_period = 20
      mitigation_timeout  = 60
    }
  }
}
