# AWS Cost Optimization System

![AWS](https://img.shields.io/badge/AWS-Cloud-orange)
![Terraform](https://img.shields.io/badge/Terraform-IaC-purple)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> An automated serverless cost monitoring and optimization system built with AWS Lambda, Terraform, and Cost Explorer API. Automatically monitors AWS spending, identifies cost-saving opportunities, and cleans up idle resources to reduce cloud waste.

![optimazer diagram](https://github.com/user-attachments/assets/861394c2-bbb8-4cfa-8041-7a5d73e25781)


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

![costoptimazation2](https://github.com/user-attachments/assets/8b6c67c2-2d76-4465-b9e1-46137b27e91f)
![costoptimazation1](https://github.com/user-attachments/assets/100cd3c9-efba-4f15-ac1a-7d2108d2fbdf)


