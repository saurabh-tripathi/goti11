output "app_url" {
  description = "Public URL of the app"
  value       = "https://${local.domain_name}"
}

output "ecr_backend_url" {
  description = "Push backend Docker image here"
  value       = module.ecr.repository_url
}

output "ecr_frontend_url" {
  description = "Push frontend Docker image here"
  value       = module.ecr.frontend_repository_url
}

output "rds_address" {
  description = "RDS host (for migrations / bastion tunnelling)"
  value       = module.rds.address
}

output "ecs_cluster" {
  value = module.ecs.cluster_name
}

output "ecs_backend_service" {
  value = module.ecs.service_name
}

output "ecs_frontend_service" {
  value = module.ecs.frontend_service_name
}

output "log_group_backend" {
  description = "CloudWatch log group — FastAPI"
  value       = module.ecs.log_group_name
}

output "log_group_frontend" {
  description = "CloudWatch log group — Nginx"
  value       = module.ecs.frontend_log_group_name
}

output "alb_dns_name" {
  description = "Raw ALB hostname (useful before DNS propagates)"
  value       = module.alb.alb_dns_name
}

output "deploy_commands" {
  description = "Paste-ready commands to build and push Docker images after first apply"
  value       = <<-EOT

    # 1 — Authenticate Docker to ECR
    aws ecr get-login-password --region us-west-2 | \
      docker login --username AWS --password-stdin ${module.ecr.repository_url}

    # 2 — Build & push backend
    docker build -t ${module.ecr.repository_url}:latest ./backend
    docker push ${module.ecr.repository_url}:latest

    # 3 — Build & push frontend
    docker build -t ${module.ecr.frontend_repository_url}:latest ./frontend
    docker push ${module.ecr.frontend_repository_url}:latest

    # 4 — Force new ECS deployments
    aws ecs update-service --cluster ${module.ecs.cluster_name} \
      --service ${module.ecs.service_name} --force-new-deployment --region us-west-2
    aws ecs update-service --cluster ${module.ecs.cluster_name} \
      --service ${module.ecs.frontend_service_name} --force-new-deployment --region us-west-2
  EOT
}
