# AWS Cost Optimization System

![AWS](https://img.shields.io/badge/AWS-Cloud-orange)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> An automated serverless cost monitoring and optimization system built with AWS Lambda, Terraform, and Cost Explorer API. Automatically monitors AWS spending, identifies cost-saving opportunities, and cleans up idle resources to reduce cloud waste.

![Architecture Diagram](docs/architecture.png)

## 🎯 Features

- ✅ **Daily Cost Monitoring** - Automated tracking of AWS spending with Cost Explorer API
- ✅ **Smart Alerting** - Email notifications when spending exceeds custom thresholds
- ✅ **Resource Cleanup** - Automatic identification and removal of idle resources
- ✅ **Cost Reports** - Historical cost data stored in S3 with lifecycle management
- ✅ **Infrastructure as Code** - Complete Terraform deployment for reproducibility
- ✅ **Serverless Architecture** - Cost-effective Lambda-based execution (~$5-10/month)
- ✅ **Multi-Region Support** - Deployable to any AWS region
- ✅ **Slack Integration** - Optional Slack webhook notifications

## 💰 Cost Savings

This system helps reduce AWS costs by automatically detecting and cleaning up:

- **Idle EC2 Instances** - Instances with <5% CPU utilization for 7 days
- **Unattached EBS Volumes** - Volumes not attached for 30+ days
- **Old EBS Snapshots** - Snapshots older than 90 days without retention tags
- **Idle Elastic IPs** - Unassociated Elastic IPs costing $3.60/month each

**Estimated Monthly Savings**: $50-500+ depending on your resource waste

## 🏗️ Architecture

┌─────────────────────────────────────────────────────────────────┐
│ AWS Cloud │
│ │
│ ┌──────────────┐ ┌──────────────┐ │
│ │ EventBridge │────────>│ Lambda │ │
│ │ (Scheduled) │ │ Cost Monitor │ │
│ └──────────────┘ └──────┬───────┘ │
│ Daily 8AM UTC │ │
│ │ │
│ v │
│ ┌────────────────┐ │
│ │ Cost Explorer │ │
│ │ API │ │
│ └────────┬───────┘ │
│ │ │
│ v │
│ ┌───────────────────────────┴─────────────────────┐ │
│ │ │ │
│ v v │
│ ┌─────────┐ ┌──────────┐ │
│ │ S3 │ │ SNS │ │
│ │ Reports │ │ Alerts │ │
│ └─────────┘ └─────┬────┘ │
│ │ │
│ ┌──────────────┐ ┌──────────────┐ │ │
│ │ EventBridge │────────>│ Lambda │ │ │
│ │ (Scheduled) │ │ Cleanup │ │ │
│ └──────────────┘ └──────┬───────┘ │ │
│ Weekly Monday 6AM │ │ │
│ │ │ │
│ v v │
│ ┌────────────────┐ ┌─────────┐ │
│ │ EC2 / EBS │ │ Email │ │
│ │ CloudWatch │ │ Slack │ │
│ └────────────────┘ └─────────┘ │
└─────────────────────────────────────────────────────────────────┘

text

## 📋 Prerequisites

- **AWS Account** with appropriate permissions
- **Terraform** >= 1.0
- **AWS CLI** configured with credentials
- **Python** 3.11+
- **Cost Explorer** enabled (wait 24 hours after enabling for data)

## 🚀 Quick Start

### 1. Clone the Repository

git clone https://github.com/yourusername/aws-cost-optimizer.git
cd aws-cost-optimizer

text

### 2. Configure AWS Credentials

aws configure

Enter your AWS Access Key ID
Enter your AWS Secret Access Key
Enter your default region (e.g., us-west-2)
text

### 3. Enable AWS Cost Explorer

1. Log into AWS Console as **root user**
2. Navigate to Cost Management → Cost Explorer
3. Click **"Enable Cost Explorer"**
4. Wait 24 hours for data to populate

### 4. Set Up Terraform Variables

cd terraform
cp terraform.tfvars.example terraform.tfvars

text

Edit `terraform.tfvars` with your settings:

aws_region = "us-west-2"
alert_email = "your-email@example.com"
daily_cost_threshold = 50.00
weekly_cost_threshold = 300.00
cleanup_enabled = false # Set true to enable cleanup
cleanup_dry_run = true # Set false for real deletions