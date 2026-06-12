terraform {
  required_version = ">= 1.9"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }

  # Uncomment to enable remote state (recommended for team use):
  # backend "s3" {
  #   bucket = "your-tf-state-bucket"
  #   key    = "app/terraform.tfstate"
  #   region = "us-east-1"
  # }
}
