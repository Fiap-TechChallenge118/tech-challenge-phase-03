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
  region = "us-east-1"
  default_tags {
    tags = {
      Project   = "tech-challenge-phase-03"
      ManagedBy = "Terraform"
      ExpiresOn = "2026-09-26"
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "state" {
  bucket        = "tc03-${data.aws_caller_identity.current.account_id}-tfstate"
  force_destroy = false
  lifecycle {
    prevent_destroy = true
  }
}
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.state.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Deny", Principal = "*", Action = "s3:*"
      Resource  = [aws_s3_bucket.state.arn, "${aws_s3_bucket.state.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}

module "ecr" {
  source = "../modules/ecr"
  name   = "tc03-triagem"
}

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}
resource "aws_iam_role" "github" {
  name = "tc03-github-ecr-develop"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow", Action = "sts:AssumeRoleWithWebIdentity"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = [
            "repo:Fiap-TechChallenge118/tech-challenge-phase-03:ref:refs/heads/develop",
            "repo:Fiap-TechChallenge118@272074241/tech-challenge-phase-03@1344333800:ref:refs/heads/develop"
          ]
        }
      }
    }]
  })
}
resource "aws_iam_role_policy" "github_ecr" {
  role = aws_iam_role.github.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
      {
        Effect   = "Allow"
        Action   = ["ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:ListImages"]
        Resource = module.ecr.arn
      }
    ]
  })
}

output "state_bucket" { value = aws_s3_bucket.state.id }
output "ecr_repository_url" { value = module.ecr.url }
output "github_role_arn" { value = aws_iam_role.github.arn }
