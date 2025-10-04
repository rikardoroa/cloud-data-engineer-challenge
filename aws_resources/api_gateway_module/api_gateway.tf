
# REST API   
resource "aws_api_gateway_rest_api" "t1_db_conn_api" {
  name        = "postgresql-conn"
  description = "RDS postgresql API connection"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}


# creating api gateway path
resource "aws_api_gateway_resource" "t1_db_conn_api_path" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  parent_id   = aws_api_gateway_rest_api.t1_db_conn_api.root_resource_id
  path_part   = "postgresql-api-conn-path"
}

# creating api gateway method for post
resource "aws_api_gateway_method" "t1_db_conn_api_post" {
  rest_api_id   = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id   = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method   = "POST"
  authorization = "NONE"
}

# post response
resource "aws_api_gateway_method_response" "response_200_post" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method = aws_api_gateway_method.t1_db_conn_api_post.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

# post integration
resource "aws_api_gateway_integration" "integration_post" {
  rest_api_id             = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id             = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method             = aws_api_gateway_method.t1_db_conn_api_post.http_method
  type                    = "AWS_PROXY"

  # Con AWS_PROXY el método de integración debe ser POST, aunque el externo sea POST o GET
  integration_http_method = "POST"
  uri                     = var.invoke_arn
}


# creating api gateway method for get
resource "aws_api_gateway_method" "t1_db_conn_api_get" {
  rest_api_id   = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id   = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method   = "GET"
  authorization = "NONE"
}

# get response
resource "aws_api_gateway_method_response" "response_200_get" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method = aws_api_gateway_method.t1_db_conn_api_get.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

# get integration
resource "aws_api_gateway_integration" "integration_get" {
  rest_api_id             = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id             = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method             = aws_api_gateway_method.t1_db_conn_api_get.http_method
  type                    = "AWS_PROXY"


  integration_http_method = "POST"
  uri                     = var.invoke_arn
}

# lambda invokation
resource "aws_lambda_permission" "allow_apigateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.function_name
  principal     = "apigateway.amazonaws.com"

  # Permite cualquier método dentro del stage dev
  source_arn = "${aws_api_gateway_rest_api.t1_db_conn_api.execution_arn}/dev/*"
}

# deployment for post and get
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id

  depends_on = [
    # POST
    aws_api_gateway_method.t1_db_conn_api_post,
    aws_api_gateway_integration.integration_post,
    aws_api_gateway_method_response.response_200_post,

    # GET
    aws_api_gateway_method.t1_db_conn_api_get,
    aws_api_gateway_integration.integration_get,
    aws_api_gateway_method_response.response_200_get,
  ]
}

resource "aws_api_gateway_stage" "postgresql_api_conn_stage" {
  rest_api_id   = aws_api_gateway_rest_api.t1_db_conn_api.id
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  stage_name    = "dev"
}


#caching and  throttling

resource "aws_api_gateway_method_settings" "api_method_settings" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  stage_name  = aws_api_gateway_stage.postgresql_api_conn_stage.stage_name
  method_path = "*/*"   # Cubre todos los verbos y rutas

  settings {
    cache_data_encrypted   = false
    cache_ttl_in_seconds   = 0
    throttling_burst_limit = 500
    throttling_rate_limit  = 1000
  }
}