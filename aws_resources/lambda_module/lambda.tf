# Connect with Docker unix socket
provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# ECR repository creation
resource "aws_ecr_repository" "lambda_repository" {
  name                 = "lambda-mv-pr-repository"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  force_delete = true

  tags = {
    Environment = "development"
  }
}

# AWS CLI login for ECR
resource "null_resource" "ecr_login" {
  provisioner "local-exec" {
    command = <<EOT
      aws ecr get-login-password --region ${var.aws_region} | \
      docker login --username AWS --password-stdin ${aws_ecr_repository.lambda_repository.repository_url}
    EOT
  }

  depends_on = [aws_ecr_repository.lambda_repository]
}

# Archive the Lambda code to detect changes
data "archive_file" "lambda_code" {
  type        = "zip"
  source_dir  = "${path.module}/resources/python/aws_lambda"
  output_path = "${path.module}/lambda_code.zip"
}

# Build and push Docker image when Lambda code changes
resource "null_resource" "docker_build_push" {
  triggers = {
    code_hash = data.archive_file.lambda_code.output_md5
  }

  provisioner "local-exec" {
    command = <<EOT
      REPO_URL=${aws_ecr_repository.lambda_repository.repository_url}
      HASH=${data.archive_file.lambda_code.output_md5}

      echo "Logging in to ECR at $REPO_URL..."
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin $REPO_URL

      echo "Building Docker image..."
      docker build -t aws_lambda:latest -f ${path.module}/resources/DockerFile ${path.module}/resources && docker tag aws_lambda:latest ${aws_ecr_repository.lambda_repository.repository_url}:latest

      echo "Tagging Docker image..."
      docker tag aws_lambda:latest $REPO_URL:$HASH
      docker tag aws_lambda:latest $REPO_URL:latest

      echo "Pushing Docker image..."
      docker push $REPO_URL:$HASH
      docker push $REPO_URL:latest
    EOT
  }

  depends_on = [
    aws_ecr_repository.lambda_repository,
    null_resource.ecr_login
  ]
}

# AWS Lambda function configuration
resource "aws_lambda_function" "lambda_function" {
  function_name = "put-mv-dt-db-lambda"
  image_uri     = "${aws_ecr_repository.lambda_repository.repository_url}:${data.archive_file.lambda_code.output_md5}"
  role          = aws_iam_role.iam_dev_role_pr_mv.arn
  package_type  = "Image"
  timeout       = var.lambda_timeout
  memory_size   = 500

  vpc_config {
    subnet_ids = [
      var.subnet2
    ]
    security_group_ids = [
      var.security_group_lambda
    ]
  }

  environment {
    variables = {
      bucket      = var.target_bucket
      key         = var.target_key
      new_db_name = var.db_name
    }
  }

  depends_on = [
    null_resource.docker_build_push
  ]
}

# adding s3 as a lambda trigger
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3InvokeLambda"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.bucket_arn
}

# notification when a object is created (Put Event) to trigger the lambda function
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = var.bucket_id

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_function.arn
    events              = ["s3:ObjectCreated:Put"]
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

# sns topic for lambda alerts
resource "aws_sns_topic" "lambda_alerts" {
  name = "lambda-alerts"
}

# alerts if the s3 event fails to trigger the lambda
resource "aws_cloudwatch_metric_alarm" "s3_event_failure_alarm" {
  alarm_name          = "S3-Event-Failure-Alarm"
  alarm_description   = "Triggered when S3 event notification to Lambda fails"
  namespace           = "AWS/S3"
  metric_name         = "EventNotificationsFailed"
  statistic           = "Sum"
  period              = 300
  threshold           = 1
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  alarm_actions       = [aws_sns_topic.lambda_alerts.arn]

  dimensions = {
    BucketName = var.bucket_id
  }
}

# alerts if the lambda fails in any case
resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  alarm_name          = "Lambda-Error-Alarm"
  alarm_description   = "Triggered when Lambda function reports errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 1
  alarm_actions       = [aws_sns_topic.lambda_alerts.arn]

  dimensions = {
    FunctionName = aws_lambda_function.lambda_function.function_name
  }
}
