locals {
  domain_name = "${var.subdomain}.${var.root_domain}"   # goti11.gradnuclei.com

  app_image      = var.app_image      != "" ? var.app_image      : "${module.ecr.repository_url}:latest"
  frontend_image = var.frontend_image != "" ? var.frontend_image : "${module.ecr.frontend_repository_url}:latest"
}

# ── Random secrets ────────────────────────────────────────────────────────────

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "random_password" "secret_key" {
  length  = 64
  special = false
}

# ── Existing Route 53 hosted zone (shared with other projects on gradnuclei.com)
# Do NOT create a new zone — one already exists from the ChaukaBartan stack.

data "aws_route53_zone" "root" {
  name         = var.root_domain
  private_zone = false
}

# ── Modules ───────────────────────────────────────────────────────────────────

module "vpc" {
  source       = "../../modules/vpc"
  project_name = var.project_name
  environment  = var.environment
}

module "ecr" {
  source       = "../../modules/ecr"
  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source       = "../../modules/rds"
  project_name = var.project_name
  environment  = var.environment

  subnet_ids  = module.vpc.isolated_subnet_ids
  rds_sg_id   = module.vpc.rds_sg_id
  db_name     = var.db_name
  db_username = var.db_username
  db_password = random_password.db.result
}

module "secrets" {
  source       = "../../modules/secrets"
  project_name = var.project_name
  environment  = var.environment

  database_url = "postgresql://${var.db_username}:${random_password.db.result}@${module.rds.address}:${module.rds.port}/${module.rds.db_name}"
  secret_key   = random_password.secret_key.result
}

module "alb" {
  source       = "../../modules/alb"
  project_name = var.project_name
  environment  = var.environment

  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.public_subnet_ids
  alb_sg_id      = module.vpc.alb_sg_id
  domain_name    = local.domain_name
  hosted_zone_id = data.aws_route53_zone.root.zone_id
}

module "ecs" {
  source       = "../../modules/ecs"
  project_name = var.project_name
  environment  = var.environment
  region       = var.region
  domain_name  = local.domain_name

  app_image      = local.app_image
  frontend_image = local.frontend_image

  subnet_ids                = module.vpc.public_subnet_ids
  ecs_sg_id                 = module.vpc.ecs_sg_id
  backend_target_group_arn  = module.alb.backend_target_group_arn
  frontend_target_group_arn = module.alb.frontend_target_group_arn

  database_url_secret_arn = module.secrets.database_url_secret_arn
  secret_key_arn          = module.secrets.secret_key_arn
  ecr_repository_arn      = module.ecr.repository_arn
}

# ── Monthly budget alert ──────────────────────────────────────────────────────
# Sends an email when the Goti11 project spend approaches $50/month.
# Tag all resources with Project=goti11 (done via provider default_tags) so
# Cost Explorer can filter by this project.

resource "aws_budgets_budget" "monthly" {
  count = var.budget_alert_email != "" ? 1 : 0

  name         = "${var.project_name}-${var.environment}-monthly"
  budget_type  = "COST"
  limit_amount = "50"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = ["user:Project$${var.project_name}"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.budget_alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.budget_alert_email]
  }
}
