# SNS topic for cost alerts
resource "aws_sns_topic" "cost_alerts" {
  name              = "${var.project_name}-cost-alerts"
  display_name      = "AWS Cost Optimization Alerts"
  
  tags = var.common_tags
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_sns_topic_subscription" "slack_alert" {
  count     = var.slack_webhook_url != "" ? 1 : 0
  topic_arn = aws_sns_topic.cost_alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.slack_notifier.arn
}

resource "aws_lambda_permission" "allow_sns_slack" {
  count         = var.slack_webhook_url != "" ? 1 : 0
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.slack_notifier.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.cost_alerts.arn
}

# Secrets Manager for Slack webhook
resource "aws_secretsmanager_secret" "slack_webhook" {
  name        = "${var.project_name}-slack-webhook"
  description = "Slack webhook URL for cost alerts"
  
  tags = var.common_tags
}

resource "aws_secretsmanager_secret_version" "slack_webhook" {
  count         = var.slack_webhook_url != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.slack_webhook.id
  secret_string = jsonencode({
    webhook_url = var.slack_webhook_url
  })
}
