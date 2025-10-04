output "target_bucket" {
  value  = aws_s3_bucket.bucket_creation.bucket
}


output "target_key"{
value = aws_kms_key.dts_kms_key.arn
}


output "bucket_id"{
  value  = aws_s3_bucket.bucket_creation.id
}

output "bucket_arn"{
  value  = aws_s3_bucket.bucket_creation.arn
}