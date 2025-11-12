# Daily cost monitoring schedule
resource "aws_cloudwatch_event_rule" "daily_cost_check" {
  name                = "${var.project_name}-daily-cost-check"
  description         = "Trigger cost monitoring Lambda daily at 8 AM UTC"
  schedule_expression = "cron(0 8 * * ? *)"
  
  tags = var.common_tags
}

resource "aws_cloudwatch_event_target" "cost_monitor" {
  rule      = aws_cloudwatch_event_rule.daily_cost_check.name
  target_id = "CostMonitorLambda"
  arn       = aws_lambda_function.cost_monitor.arn
}

resource "aws_lambda_permission" "allow_eventbridge_cost_monitor" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_monitor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_cost_check.arn
}

# Weekly resource cleanup schedule
resource "aws_cloudwatch_event_rule" "weekly_cleanup" {
  name                = "${var.project_name}-weekly-cleanup"
  description         = "Trigger resource cleanup Lambda weekly on Monday at 6 AM UTC"
  schedule_expression = "cron(0 6 ? * MON *)"
  
  tags = var.common_tags
}

resource "aws_cloudwatch_event_target" "resource_cleanup" {
  rule      = aws_cloudwatch_event_rule.weekly_cleanup.name
  target_id = "ResourceCleanupLambda"
  arn       = aws_lambda_function.resource_cleanup.arn
}

resource "aws_lambda_permission" "allow_eventbridge_cleanup" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.resource_cleanup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_cleanup.arn
}
