variable "project_name" { type = string }
variable "environment"  { type = string }
variable "vpc_id"       { type = string }
variable "subnet_ids"   { type = list(string) }
variable "alb_sg_id"    { type = string }

variable "app_port" {
  type    = number
  default = 8000
}

variable "frontend_port" {
  type    = number
  default = 80   # nginx serving static Vite files
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "domain_name" {
  type    = string
  default = ""
}

variable "hosted_zone_id" {
  type    = string
  default = ""
}
