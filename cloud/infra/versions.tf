terraform {
  required_version = ">= 1.5.0"
  required_providers {
    cloudflare = { source = "cloudflare/cloudflare", version = "~> 5.0" }
  }
  # Planned migration: move state to a locked R2 backend once A1 resources exist.
  backend "local" {}
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
