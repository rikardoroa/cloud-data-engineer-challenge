
# Creates the main API Gateway REST API.
# This defines the root API container for both GET and POST methods.
resource "aws_api_gateway_rest_api" "t1_db_conn_api" {
  name        = "postgresql-conn"
  description = "RDS postgresql API connection"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}


# Creates a specific resource path under the root of the API.
resource "aws_api_gateway_resource" "t1_db_conn_api_path" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  parent_id   = aws_api_gateway_rest_api.t1_db_conn_api.root_resource_id
  path_part   = "postgresql-api-conn-path"
}

# Defines the POST HTTP method for the API resource.
resource "aws_api_gateway_method" "t1_db_conn_api_post" {
  rest_api_id   = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id   = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method   = "POST"
  authorization = "NONE"
}

# Defines the expected 200 OK response for POST requests.
resource "aws_api_gateway_method_response" "response_200_post" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method = aws_api_gateway_method.t1_db_conn_api_post.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

# Integrates the POST method with the target Lambda function using AWS_PROXY.
# AWS_PROXY means API Gateway passes the full request directly to Lambda.
resource "aws_api_gateway_integration" "integration_post" {
  rest_api_id             = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id             = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method             = aws_api_gateway_method.t1_db_conn_api_post.http_method
  type                    = "AWS_PROXY"

  # With AWS_PROXY integration, the integration method must always be POST
  # even if the external method (client request) is GET or POST.
  integration_http_method = "POST"
  uri                     = var.invoke_arn
}


# Defines the GET HTTP method for the same API resource.
resource "aws_api_gateway_method" "t1_db_conn_api_get" {
  rest_api_id   = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id   = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method   = "GET"
  authorization = "NONE"
}

# Defines the expected 200 OK response for GET requests.
resource "aws_api_gateway_method_response" "response_200_get" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method = aws_api_gateway_method.t1_db_conn_api_get.http_method
  status_code = "200"

  response_models = {
    "application/json" = "Empty"
  }
}

# Integrates the GET method with the same Lambda function using AWS_PROXY.
# The integration method must remain POST when using AWS_PROXY.
resource "aws_api_gateway_integration" "integration_get" {
  rest_api_id             = aws_api_gateway_rest_api.t1_db_conn_api.id
  resource_id             = aws_api_gateway_resource.t1_db_conn_api_path.id
  http_method             = aws_api_gateway_method.t1_db_conn_api_get.http_method
  type                    = "AWS_PROXY"


  integration_http_method = "POST"
  uri                     = var.invoke_arn
}

# Grants API Gateway permission to invoke the Lambda function.
resource "aws_lambda_permission" "allow_apigateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.function_name
  principal     = "apigateway.amazonaws.com"


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

# Creates the "dev" stage for the API Gateway deployment.
# This defines the URL stage used in the final endpoint.
resource "aws_api_gateway_stage" "postgresql_api_conn_stage" {
  rest_api_id   = aws_api_gateway_rest_api.t1_db_conn_api.id
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  stage_name    = "dev"
}


#caching and  throttling
resource "aws_api_gateway_method_settings" "api_method_settings" {
  rest_api_id = aws_api_gateway_rest_api.t1_db_conn_api.id
  stage_name  = aws_api_gateway_stage.postgresql_api_conn_stage.stage_name
  method_path = "*/*"   

  settings {
    cache_data_encrypted   = false
    cache_ttl_in_seconds   = 0
    throttling_burst_limit = 500
    throttling_rate_limit  = 1000
  }
}