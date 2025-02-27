resource "aws_apigatewayv2_api" "tetris_api" {
  name          = var.api_gateway_name
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "tetris_api_stage" {
    api_id = aws_apigatewayv2_api.tetris_api.id
    name = var.api_gateway_stage_name
    auto_deploy = true
    route_settings {
      route_key = "POST /score_evaluation"
      logging_level = "ERROR"
      throttling_rate_limit = 10
      throttling_burst_limit = 10
    }
    access_log_settings {
      destination_arn = aws_cloudwatch_log_group.apigateway_accesslog.arn
      format = var.api_gateway_access_log_format
    }
}

resource "aws_apigatewayv2_integration" "send_message_to_sqs_lambda_integration" {
  api_id = aws_apigatewayv2_api.tetris_api.id
  integration_uri = aws_lambda_function.function.invoke_arn
  integration_type = "AWS_PROXY"
  integration_method = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "send_message_lambda" {
  api_id = aws_apigatewayv2_api.tetris_api.id
  route_key = "POST /score_evaluation"
  target = "integrations/${aws_apigatewayv2_integration.send_message_to_sqs_lambda_integration.id}"
}
