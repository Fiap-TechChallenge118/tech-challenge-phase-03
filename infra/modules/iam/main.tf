variable "name" { type = string }
variable "model_arn" { type = string }
variable "datasets_arn" { type = string }
variable "repository_arn" { type = string }
locals {
  ecs_trust = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "ecs-tasks.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}
resource "aws_iam_role" "execution" {
  name               = "${var.name}-execution"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy" "execution" {
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
      { Effect = "Allow", Action = ["ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"], Resource = var.repository_arn },
      { Effect = "Allow", Action = ["logs:CreateLogStream", "logs:PutLogEvents"], Resource = "arn:aws:logs:*:*:log-group:/ecs/${var.name}:*" }
    ]
  })
}
resource "aws_iam_role" "inference" {
  name               = "${var.name}-inference"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy" "inference" {
  role = aws_iam_role.inference.id
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Action = ["s3:GetObject"], Resource = "${var.model_arn}/models/*" }]
  })
}
resource "aws_iam_role" "training" {
  name               = "${var.name}-training"
  assume_role_policy = local.ecs_trust
}
resource "aws_iam_role_policy" "training" {
  role = aws_iam_role.training.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3:ListBucket"], Resource = [var.datasets_arn, var.model_arn] },
      { Effect = "Allow", Action = ["s3:GetObject"], Resource = "${var.datasets_arn}/*" },
      { Effect = "Allow", Action = ["s3:PutObject", "s3:GetObject"], Resource = ["${var.datasets_arn}/processed/*", "${var.model_arn}/models/*"] }
    ]
  })
}
output "execution_role_arn" { value = aws_iam_role.execution.arn }
output "inference_role_arn" { value = aws_iam_role.inference.arn }
output "training_role_arn" { value = aws_iam_role.training.arn }
