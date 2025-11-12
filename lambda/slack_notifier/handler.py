import json
import os
import boto3
import urllib3

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')
http = urllib3.PoolManager()

# Environment variables
SLACK_SECRET_ARN = os.environ['SLACK_SECRET_ARN']


def lambda_handler(event, context):
    """
    Send SNS notifications to Slack
    """
    try:
        # Get Slack webhook URL from Secrets Manager
        webhook_url = get_slack_webhook()
        
        if not webhook_url:
            print("No Slack webhook configured")
            return {'statusCode': 200, 'body': 'No webhook configured'}
        
        # Parse SNS message
        sns_message = event['Records'][0]['Sns']
        subject = sns_message['Subject']
        message = sns_message['Message']
        
        # Format Slack message
        slack_payload = format_slack_message(subject, message)
        
        # Send to Slack
        response = http.request(
            'POST',
            webhook_url,
            body=json.dumps(slack_payload),
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Slack response: {response.status}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Notification sent to Slack')
        }
        
    except Exception as e:
        print(f"Error sending to Slack: {str(e)}")
        raise


def get_slack_webhook():
    """
    Retrieve Slack webhook URL from Secrets Manager
    """
    try:
        response = secrets_client.get_secret_value(SecretId=SLACK_SECRET_ARN)
        secret = json.loads(response['SecretString'])
        return secret.get('webhook_url', '')
    except Exception as e:
        print(f"Error retrieving Slack webhook: {str(e)}")
        return ''


def format_slack_message(subject, message):
    """
    Format message for Slack with blocks for better presentation
    """
    # Determine color based on subject
    color = '#36a64f'  # Green default
    if 'Alert' in subject or '⚠️' in subject:
        color = '#ff9900'  # Orange for alerts
    elif 'Error' in subject or '❌' in subject:
        color = '#ff0000'  # Red for errors
    
    # Create Slack blocks
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": subject,
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"``````"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Timestamp:* <!date^{int(boto3.client('sts').get_caller_identity()['Account'])}^{{date_short_pretty}} at {{time}}|now>"
                }
            ]
        }
    ]
    
    return {
        "attachments": [
            {
                "color": color,
                "blocks": blocks
            }
        ]
    }
