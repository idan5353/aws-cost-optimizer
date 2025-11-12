# Archive Lambda function code
data "archive_file" "cost_monitor_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/cost_monitor"
  output_path = "${path.module}/../builds/cost_monitor.zip"
}

data "archive_file" "resource_cleanup_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/resource_cleanup"
  output_path = "${path.module}/../builds/resource_cleanup.zip"
}

data "archive_file" "slack_notifier_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/slack_notifier"
  output_path = "${path.module}/../builds/slack_notifier.zip"
}

# Cost Monitor Lambda Function
resource "aws_lambda_function" "cost_monitor" {
  function_name = "${var.project_name}-cost-monitor"
  description   = "Monitor AWS costs and send alerts"
  
  filename         = data.archive_file.cost_monitor_zip.output_path
  source_code_hash = data.archive_file.cost_monitor_zip.output_base64sha256
  
  handler = "handler.lambda_handler"
  runtime = "python3.11"
  timeout = 300
  memory_size = 512
  
  role = aws_iam_role.lambda_cost_monitor.arn
  
  environment {
    variables = {
      DAILY_COST_THRESHOLD  = var.daily_cost_threshold
      WEEKLY_COST_THRESHOLD = var.weekly_cost_threshold
      S3_BUCKET             = aws_s3_bucket.cost_reports.id
      SNS_TOPIC_ARN         = aws_sns_topic.cost_alerts.arn
      SLACK_SECRET_ARN      = aws_secretsmanager_secret.slack_webhook.arn
      AWS_ACCOUNT_ID        = data.aws_caller_identity.current.account_id
    }
  }
  
  tags = merge(var.common_tags, {
    Name = "Cost Monitor Lambda"
  })
}

resource "aws_cloudwatch_log_group" "cost_monitor" {
  name              = "/aws/lambda/${aws_lambda_function.cost_monitor.function_name}"
  retention_in_days = 14
  
  tags = var.common_tags
}

# Resource Cleanup Lambda Function
resource "aws_lambda_function" "resource_cleanup" {
  function_name = "${var.project_name}-resource-cleanup"
  description   = "Identify and cleanup idle AWS resources"
  
  filename         = data.archive_file.resource_cleanup_zip.output_path
  source_code_hash = data.archive_file.resource_cleanup_zip.output_base64sha256
  
  handler = "handler.lambda_handler"
  runtime = "python3.11"
  timeout = 600
  memory_size = 1024
  
  role = aws_iam_role.lambda_resource_cleanup.arn
  
  environment {
    variables = {
      DRY_RUN            = tostring(var.cleanup_dry_run)
      CLEANUP_ENABLED    = tostring(var.cleanup_enabled)
      CPU_THRESHOLD      = var.cpu_threshold_percent
      VOLUME_AGE_DAYS    = var.volume_age_days
      SNAPSHOT_AGE_DAYS  = var.snapshot_age_days
      S3_BUCKET          = aws_s3_bucket.cost_reports.id
      SNS_TOPIC_ARN      = aws_sns_topic.cost_alerts.arn
    }
  }
  
  tags = merge(var.common_tags, {
    Name = "Resource Cleanup Lambda"
  })
}

resource "aws_cloudwatch_log_group" "resource_cleanup" {
  name              = "/aws/lambda/${aws_lambda_function.resource_cleanup.function_name}"
  retention_in_days = 14
  
  tags = var.common_tags
}

# Slack Notifier Lambda Function
resource "aws_lambda_function" "slack_notifier" {
  function_name = "${var.project_name}-slack-notifier"
  description   = "Send cost alerts to Slack"
  
  filename         = data.archive_file.slack_notifier_zip.output_path
  source_code_hash = data.archive_file.slack_notifier_zip.output_base64sha256
  
  handler = "handler.lambda_handler"
  runtime = "python3.11"
  timeout = 60
  memory_size = 256
  
  role = aws_iam_role.lambda_slack_notifier.arn
  
  environment {
    variables = {
      SLACK_SECRET_ARN = aws_secretsmanager_secret.slack_webhook.arn
    }
  }
  
  tags = merge(var.common_tags, {
    Name = "Slack Notifier Lambda"
  })
}

resource "aws_cloudwatch_log_group" "slack_notifier" {
  name              = "/aws/lambda/${aws_lambda_function.slack_notifier.function_name}"
  retention_in_days = 7
  
  tags = var.common_tags
}
