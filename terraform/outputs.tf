output "cost_reports_bucket" {
  description = "S3 bucket for cost reports"
  value       = aws_s3_bucket.cost_reports.id
}

output "lambda_deployments_bucket" {
  description = "S3 bucket for Lambda deployments"
  value       = aws_s3_bucket.lambda_deployments.id
}

output "cost_monitor_function_name" {
  description = "Cost monitor Lambda function name"
  value       = aws_lambda_function.cost_monitor.function_name
}

output "resource_cleanup_function_name" {
  description = "Resource cleanup Lambda function name"
  value       = aws_lambda_function.resource_cleanup.function_name
}

output "slack_notifier_function_name" {
  description = "Slack notifier Lambda function name"
  value       = aws_lambda_function.slack_notifier.function_name
}

output "sns_topic_arn" {
  description = "SNS topic ARN for cost alerts"
  value       = aws_sns_topic.cost_alerts.arn
}

