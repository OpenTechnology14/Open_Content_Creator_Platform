# Cloud Relay Infrastructure — DigitalOcean
#
# Provisions the multi-tenant relay infrastructure:
# - Droplet ($12/mo) — runs FastAPI relay + Tailscale
# - Managed Postgres ($15/mo) — multi-tenant with RLS
# - Spaces ($5/mo) — per-tenant asset storage
#
# Total base cost: ~$32/month
#
# Usage:
#   cd cloud/terraform
#   terraform init
#   terraform plan
#   terraform apply

terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.do_token
}

# ============================================================
# Variables
# ============================================================

variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "droplet_size" {
  description = "Droplet size slug"
  type        = string
  default     = "s-2vcpu-4gb"  # $24/mo — upgrade to s-4vcpu-8gb when needed
}

variable "domain" {
  description = "Primary domain (e.g., streamextend.com)"
  type        = string
  default     = "streamextend.com"
}

variable "ssh_key_fingerprint" {
  description = "SSH key fingerprint for droplet access"
  type        = string
}

# ============================================================
# Droplet — Relay API server
# ============================================================

resource "digitalocean_droplet" "relay" {
  name     = "relay-api"
  region   = var.region
  size     = var.droplet_size
  image    = "ubuntu-24-04-x64"
  ssh_keys = [var.ssh_key_fingerprint]

  user_data = <<-EOF
    #!/bin/bash
    # Initial setup
    apt-get update && apt-get upgrade -y
    apt-get install -y docker.io docker-compose-v2 python3-pip

    # Install Tailscale
    curl -fsSL https://tailscale.com/install.sh | sh

    # Create app directory
    mkdir -p /opt/relay-api
    cd /opt/relay-api

    # Docker will be configured by CI/CD pipeline
    echo "Droplet provisioned — deploy via CI/CD"
  EOF

  tags = ["relay", "production"]
}

# ============================================================
# Managed Postgres — Multi-tenant database
# ============================================================

resource "digitalocean_database_cluster" "postgres" {
  name       = "relay-db"
  engine     = "pg"
  version    = "16"
  size       = "db-s-1vcpu-1gb"  # $15/mo — smallest managed
  region     = var.region
  node_count = 1

  tags = ["relay", "production"]
}

resource "digitalocean_database_db" "relay" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "relay"
}

resource "digitalocean_database_user" "relay_app" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "relay_app"
}

# Restrict database access to the droplet only
resource "digitalocean_database_firewall" "relay_fw" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "droplet"
    value = digitalocean_droplet.relay.id
  }
}

# ============================================================
# Spaces — Per-tenant asset storage (S3-compatible)
# ============================================================

resource "digitalocean_spaces_bucket" "assets" {
  name   = "hcp-assets"
  region = var.region
  acl    = "private"

  lifecycle_rule {
    enabled = true
    expiration {
      days = 365  # Auto-cleanup after 1 year for free tier
    }
  }
}

# CDN for public asset delivery (optional)
resource "digitalocean_cdn" "assets_cdn" {
  origin = digitalocean_spaces_bucket.assets.bucket_domain_name
}

# ============================================================
# Firewall
# ============================================================

resource "digitalocean_firewall" "relay" {
  name        = "relay-firewall"
  droplet_ids = [digitalocean_droplet.relay.id]

  # SSH
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0"]
  }

  # HTTPS (relay API + WebSocket)
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0"]
  }

  # HTTP (redirect to HTTPS)
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0"]
  }

  # All outbound
  outbound_rule {
    protocol              = "tcp"
    port_range            = "all"
    destination_addresses = ["0.0.0.0/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "all"
    destination_addresses = ["0.0.0.0/0"]
  }
}

# ============================================================
# DNS (if managing domain via DO)
# ============================================================

resource "digitalocean_domain" "main" {
  name = var.domain
}

resource "digitalocean_record" "relay" {
  domain = digitalocean_domain.main.id
  type   = "A"
  name   = "relay"
  value  = digitalocean_droplet.relay.ipv4_address
  ttl    = 300
}

# ============================================================
# Outputs
# ============================================================

output "droplet_ip" {
  value = digitalocean_droplet.relay.ipv4_address
}

output "database_uri" {
  value     = digitalocean_database_cluster.postgres.uri
  sensitive = true
}

output "spaces_endpoint" {
  value = "https://${var.region}.digitaloceanspaces.com"
}

output "relay_url" {
  value = "https://relay.${var.domain}"
}
