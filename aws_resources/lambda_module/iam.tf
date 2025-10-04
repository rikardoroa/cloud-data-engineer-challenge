# Lambda IAM Role
resource "aws_iam_role" "iam_dev_role_pr_mv" {
  name = "iam_for_dev_pr_mv"

  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Lambda Policy Document
data "aws_iam_policy_document" "pipeline_dev_policy_pr_mv" {
  statement {
    sid    = "CloudWatchLogging"
    effect = "Allow"
    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:GetLogEvents",
      "logs:FilterLogEvents",
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutRetentionPolicy",
      "logs:DeleteLogGroup",
      "logs:DeleteLogStream"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "S3AndKMSAccess"
    effect = "Allow"
    actions = [
      "s3:ListBucket",
      "s3:GetBucketLocation",
      "s3:CreateBucket",
      "s3:DeleteBucket",
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "kms:*"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "SecretsManagerAccess"
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "EC2NetworkInterfaceAccess"
    effect = "Allow"
    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface",
      "ec2:AssignPrivateIpAddresses",
      "ec2:UnassignPrivateIpAddresses"
    ]
    resources = ["*"]
  }
}

# Attach Inline Policy to Role
resource "aws_iam_role_policy" "lambda_permissions" {
  name   = "lambda_logging_with_layer"
  role   = aws_iam_role.iam_dev_role_pr_mv.name
  policy = data.aws_iam_policy_document.pipeline_dev_policy_pr_mv.json
}
