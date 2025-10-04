data "aws_caller_identity" "current" {}

# Creating the KMS key resource
resource "aws_kms_key" "dts_kms_key" {
  description = "Key for encryption"
  enable_key_rotation = true
  key_spec = "SYMMETRIC_DEFAULT"
}

# Activating KMS key policy
resource "aws_kms_key_policy" "bucket_kms_key" {
  key_id = aws_kms_key.dts_kms_key.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id = "key-default-1"
    Statement = [
      {
        Sid = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action = "kms:*"
        Resource = "*"
      }
    ]
  })
}

# Creating KMS key alias
resource "aws_kms_alias" "dts_kms_alias" {
  name = "alias/mv-pr-dt-key"
  target_key_id = aws_kms_key.dts_kms_key.key_id
}

# Creating the S3 bucket
resource "aws_s3_bucket" "bucket_creation" {
  bucket = var.curated_bucket
  force_destroy = true
}

# Setting bucket access
resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket = aws_s3_bucket.bucket_creation.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

# Setting up bucket encryption with the KMS key
resource "aws_s3_bucket_server_side_encryption_configuration" "ss_kms_key" {
  bucket = aws_s3_bucket.bucket_creation.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
      kms_master_key_id = aws_kms_key.dts_kms_key.arn
    }
  }
}
