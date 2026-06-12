module "hostinger" {
  source = "./modules/hostinger"

  app_name    = var.app_name
  api_key     = var.hostinger_api_key
  vps_plan    = var.hostinger_vps_plan
  region      = var.hostinger_region
}

module "cloudflare" {
  source = "./modules/cloudflare"

  zone_id      = var.cloudflare_zone_id
  domain       = var.domain
  app_name     = var.app_name
  vps_ip       = module.hostinger.vps_ip
  api_token    = var.cloudflare_api_token
}

module "coolify" {
  source = "./modules/coolify"

  coolify_url   = var.coolify_url
  coolify_token = var.coolify_token
  app_name      = var.app_name
  domain        = var.domain
}
