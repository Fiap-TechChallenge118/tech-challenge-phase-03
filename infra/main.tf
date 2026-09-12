terraform {
  required_version = ">= 1.10, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
provider "aws" {
  region = var.region
  default_tags {
    tags = {
      Project   = "tech-challenge-phase-03"
      ManagedBy = "Terraform"
      ExpiresOn = var.expires_on
    }
  }
}
data "aws_caller_identity" "current" {}

module "networking" {
  source = "./modules/networking"
  name   = var.name
}
module "s3" {
  source = "./modules/s3"
  name   = "${var.name}-${data.aws_caller_identity.current.account_id}"
}
module "iam" {
  source         = "./modules/iam"
  name           = var.name
  model_arn      = module.s3.models_arn
  datasets_arn   = module.s3.datasets_arn
  repository_arn = "arn:aws:ecr:${var.region}:${data.aws_caller_identity.current.account_id}:repository/${var.name}"
}
module "monitoring" {
  source = "./modules/monitoring"
  name   = var.name
}
module "alb" {
  count             = var.enable_inference ? 1 : 0
  source            = "./modules/alb"
  name              = var.name
  vpc_id            = module.networking.vpc_id
  subnet_ids        = module.networking.public_subnet_ids
  security_group_id = module.networking.alb_security_group_id
}
module "ecs" {
  source            = "./modules/ecs"
  name              = var.name
  region            = var.region
  image_uri         = var.image_uri
  enable_inference  = var.enable_inference
  target_group_arn  = try(module.alb[0].target_group_arn, null)
  subnet_ids        = module.networking.public_subnet_ids
  security_group_id = module.networking.ecs_security_group_id
  execution_role    = module.iam.execution_role_arn
  inference_role    = module.iam.inference_role_arn
  training_role     = module.iam.training_role_arn
  model_bucket      = module.s3.models_bucket
  datasets_bucket   = module.s3.datasets_bucket
  model_key         = var.model_key
  use_onnx          = var.use_onnx
  training_command  = var.training_command
  log_group         = module.monitoring.log_group_name
  depends_on        = [module.alb, module.iam]
}
