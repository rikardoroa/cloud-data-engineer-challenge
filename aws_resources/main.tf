module "bucket_utils" {
  source        = "./bucket_module"
}


module "aws_network_utils"{
  source = "./network_module"
}


module "aws_lambda_utils" {
  source       = "./lambda_module"
  target_bucket = module.bucket_utils.target_bucket
  target_key =  module.bucket_utils.target_key
  bucket_arn =  module.bucket_utils.bucket_arn
  bucket_id =   module.bucket_utils.bucket_id
  security_group_lambda = module.aws_network_utils.security_group_lambda
  subnet2 =  module.aws_network_utils.subnet2

}


module "aws_rds_utils"{
  source     = "./rds_module"
  db_password = var.db_password
  db_user =  var.db_user
  db_name = var.db_name
  security_group = module.aws_network_utils.security_group
  subnet_group = module.aws_network_utils.subnet_group

}


module "aws_api_gateway_utils"{
  source = "./api_gateway_module"
  invoke_arn = module.aws_lambda_utils.invoke_arn
  function_name = module.aws_lambda_utils.lambda_function

}