import json
import os
import boto3
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize AWS clients
ce_client = boto3.client('ce', region_name='us-east-1')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')
secrets_client = boto3.client('secretsmanager')

# Environment variables
DAILY_THRESHOLD = float(os.environ['DAILY_COST_THRESHOLD'])
WEEKLY_THRESHOLD = float(os.environ['WEEKLY_COST_THRESHOLD'])
S3_BUCKET = os.environ['S3_BUCKET']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
SLACK_SECRET_ARN = os.environ.get('SLACK_SECRET_ARN', '')
ACCOUNT_ID = os.environ['AWS_ACCOUNT_ID']


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Main Lambda handler for cost monitoring
    """
    try:
        print("Starting cost monitoring...")
        
        # Get current date
        end_date = datetime.now().date()
        daily_start = end_date - timedelta(days=1)
        weekly_start = end_date - timedelta(days=7)
        
        # Fetch daily costs
        daily_cost = get_daily_cost(str(daily_start), str(end_date))
        
        # Fetch weekly costs
        weekly_cost = get_weekly_cost(str(weekly_start), str(end_date))
        
        # Get cost breakdown by service
        service_costs = get_cost_by_service(str(weekly_start), str(end_date))
        
        # Get top 5 services
        top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Create cost report
        report = {
            'timestamp': str(datetime.now()),
            'account_id': ACCOUNT_ID,
            'daily_cost': daily_cost,
            'weekly_cost': weekly_cost,
            'daily_threshold': DAILY_THRESHOLD,
            'weekly_threshold': WEEKLY_THRESHOLD,
            'top_services': dict(top_services),
            'all_service_costs': service_costs
        }
        
        # Save report to S3
        save_report_to_s3(report, end_date)
        
        # Check thresholds and send alerts
        alert_sent = False
        if daily_cost > DAILY_THRESHOLD:
            send_alert(
                f"⚠️ Daily Cost Alert",
                f"Daily cost ${daily_cost:.2f} exceeded threshold ${DAILY_THRESHOLD:.2f}",
                report
            )
            alert_sent = True
        
        if weekly_cost > WEEKLY_THRESHOLD:
            send_alert(
                f"⚠️ Weekly Cost Alert",
                f"Weekly cost ${weekly_cost:.2f} exceeded threshold ${WEEKLY_THRESHOLD:.2f}",
                report
            )
            alert_sent = True
        
        # Send daily summary even if no alert
        if not alert_sent:
            send_summary(report)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Cost monitoring completed successfully',
                'daily_cost': daily_cost,
                'weekly_cost': weekly_cost
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error in cost monitoring: {str(e)}")
        send_error_alert(str(e))
        raise


def get_daily_cost(start_date, end_date):
    """
    Get daily AWS costs using Cost Explorer API
    """
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        total_cost = 0
        for result in response['ResultsByTime']:
            cost = float(result['Total']['UnblendedCost']['Amount'])
            total_cost += cost
        
        print(f"Daily cost: ${total_cost:.2f}")
        return total_cost
        
    except Exception as e:
        print(f"Error fetching daily cost: {str(e)}")
        raise


def get_weekly_cost(start_date, end_date):
    """
    Get weekly AWS costs using Cost Explorer API
    """
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        total_cost = 0
        for result in response['ResultsByTime']:
            cost = float(result['Total']['UnblendedCost']['Amount'])
            total_cost += cost
        
        print(f"Weekly cost: ${total_cost:.2f}")
        return total_cost
        
    except Exception as e:
        print(f"Error fetching weekly cost: {str(e)}")
        raise


def get_cost_by_service(start_date, end_date):
    """
    Get cost breakdown by AWS service
    """
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        service_costs = {}
        for result in response['ResultsByTime']:
            for group in result['Groups']:
                service = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if service in service_costs:
                    service_costs[service] += cost
                else:
                    service_costs[service] = cost
        
        return service_costs
        
    except Exception as e:
        print(f"Error fetching cost by service: {str(e)}")
        raise


def save_report_to_s3(report, date):
    """
    Save cost report to S3
    """
    try:
        key = f"daily-reports/{date.year}/{date.month:02d}/{date.day:02d}/cost-report.json"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(report, indent=2, cls=DecimalEncoder),
            ContentType='application/json'
        )
        
        print(f"Report saved to s3://{S3_BUCKET}/{key}")
        
    except Exception as e:
        print(f"Error saving report to S3: {str(e)}")
        raise


def send_alert(title, message, report):
    """
    Send cost alert via SNS
    """
    try:
        top_services_text = "\n".join([
            f"  • {service}: ${cost:.2f}"
            for service, cost in report['top_services'].items()
        ])
        
        alert_message = f"""
{title}

{message}

📊 Cost Summary:
  • Daily Cost: ${report['daily_cost']:.2f}
  • Weekly Cost: ${report['weekly_cost']:.2f}
  • Account: {report['account_id']}

💰 Top 5 Services:
{top_services_text}

🔍 View detailed report: s3://{S3_BUCKET}/daily-reports/
        """
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=title,
            Message=alert_message
        )
        
        print(f"Alert sent: {title}")
        
    except Exception as e:
        print(f"Error sending alert: {str(e)}")


def send_summary(report):
    """
    Send daily cost summary
    """
    try:
        top_services_text = "\n".join([
            f"  • {service}: ${cost:.2f}"
            for service, cost in list(report['top_services'].items())[:3]
        ])
        
        summary_message = f"""
📈 Daily AWS Cost Summary

✅ All costs within thresholds

💰 Cost Overview:
  • Yesterday: ${report['daily_cost']:.2f}
  • Last 7 Days: ${report['weekly_cost']:.2f}

🔝 Top Services:
{top_services_text}
        """
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Daily AWS Cost Summary",
            Message=summary_message
        )
        
        print("Daily summary sent")
        
    except Exception as e:
        print(f"Error sending summary: {str(e)}")


def send_error_alert(error_message):
    """
    Send error alert
    """
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="❌ Cost Monitoring Error",
            Message=f"Error in cost monitoring Lambda:\n\n{error_message}"
        )
    except Exception as e:
        print(f"Error sending error alert: {str(e)}")
