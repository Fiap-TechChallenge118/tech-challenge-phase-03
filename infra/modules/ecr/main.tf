variable "name" { type = string }
resource "aws_ecr_repository" "this" {
  name                 = var.name
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  image_scanning_configuration { scan_on_push = true }
}
resource "aws_ecr_lifecycle_policy" "this" {
  repository = aws_ecr_repository.this.name
  policy = jsonencode({ rules = [{
    rulePriority = 1
    description  = "Remove camadas sem tag após 14 dias"
    selection = {
      tagStatus = "untagged", countType = "sinceImagePushed", countUnit = "days", countNumber = 14
    }
    action = { type = "expire" }
  }] })
}
output "arn" { value = aws_ecr_repository.this.arn }
output "url" { value = aws_ecr_repository.this.repository_url }
