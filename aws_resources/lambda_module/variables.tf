variable "lambda_timeout" {
  description = "The timeout for the Lambda function in seconds"
  type        = number
  default     = 360 # 6 minutes
}

variable "aws_region"{
  description = "aws region"
  type = string
  default = "us-east-2"
}


variable "target_bucket" {
  type=string
}

variable "target_key" {
  type=string
}


variable "bucket_id"{
  type=string
}

variable "bucket_arn"{
  type=string
}