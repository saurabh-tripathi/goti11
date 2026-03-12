terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Uncomment once you have an S3 bucket for remote state:
  # backend "s3" {
  #   bucket         = "goti11-tfstate"
  #   key            = "dev/terraform.tfstate"
  #   region         = "us-west-2"
  #   dynamodb_table = "goti11-tflock"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project     = var.project_name
      Application = "Goti11"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "random" {}
