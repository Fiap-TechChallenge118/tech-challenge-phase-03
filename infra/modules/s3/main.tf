variable "name" { type = string }
resource "aws_s3_bucket" "this" {
  for_each      = toset(["models", "datasets"])
  bucket        = "${var.name}-${each.key}"
  force_destroy = false
}
resource "aws_s3_bucket_public_access_block" "this" {
  for_each                = aws_s3_bucket.this
  bucket                  = each.value.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_versioning" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.id
  versioning_configuration { status = "Enabled" }
}
resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}
resource "aws_s3_bucket_policy" "this" {
  for_each = aws_s3_bucket.this
  bucket   = each.value.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Deny", Principal = "*", Action = "s3:*"
      Resource  = [each.value.arn, "${each.value.arn}/*"]
      Condition = { Bool = { "aws:SecureTransport" = "false" } }
    }]
  })
}
output "models_bucket" { value = aws_s3_bucket.this["models"].id }
output "datasets_bucket" { value = aws_s3_bucket.this["datasets"].id }
output "models_arn" { value = aws_s3_bucket.this["models"].arn }
output "datasets_arn" { value = aws_s3_bucket.this["datasets"].arn }
