variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "cost-optimizer"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "daily_cost_threshold" {
  description = "Daily cost threshold in USD for alerts"
  type        = number
  default     = 100.00
}

variable "weekly_cost_threshold" {
  description = "Weekly cost threshold in USD for alerts"
  type        = number
  default     = 500.00
}

variable "alert_email" {
  description = "Email address for cost alerts"
  type        = string
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "cleanup_enabled" {
  description = "Enable automated resource cleanup"
  type        = bool
  default     = false
}

variable "cleanup_dry_run" {
  description = "Run cleanup in dry-run mode (no actual deletions)"
  type        = bool
  default     = true
}

variable "cpu_threshold_percent" {
  description = "CPU utilization threshold for idle EC2 detection"
  type        = number
  default     = 5
}

variable "volume_age_days" {
  description = "Age in days for unattached EBS volumes to be flagged"
  type        = number
  default     = 30
}

variable "snapshot_age_days" {
  description = "Age in days for old snapshots to be flagged"
  type        = number
  default     = 90
}

variable "cost_anomaly_threshold" {
  description = "Cost anomaly detection threshold in USD"
  type        = number
  default     = 100
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "CostOptimization"
    ManagedBy   = "Terraform"
    Owner       = "DevOps"
  }
}
