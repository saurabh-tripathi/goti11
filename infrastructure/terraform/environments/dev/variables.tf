variable "project_name" {
  type    = string
  default = "goti11"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "region" {
  type    = string
  default = "us-west-2"
}

variable "db_name" {
  type    = string
  default = "goti11"
}

variable "db_username" {
  type    = string
  default = "goti11admin"
}

variable "app_image" {
  type        = string
  description = "Backend ECR image URI. Leave empty on first apply; fill after pushing."
  default     = ""
}

variable "frontend_image" {
  type        = string
  description = "Frontend ECR image URI. Leave empty on first apply; fill after pushing."
  default     = ""
}

variable "root_domain" {
  type        = string
  description = "Root domain already in Route 53 (gradnuclei.com). Used to look up the existing hosted zone."
  default     = "gradnuclei.com"
}

variable "subdomain" {
  type        = string
  description = "Subdomain for this project → goti11.gradnuclei.com"
  default     = "goti11"
}

variable "budget_alert_email" {
  type        = string
  description = "Email address for monthly budget alerts."
  default     = ""
}
