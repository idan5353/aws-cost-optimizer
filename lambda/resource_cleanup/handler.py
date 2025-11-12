import json
import os
import boto3
from datetime import datetime, timedelta
from typing import List, Dict

# Initialize AWS clients
ec2_client = boto3.client('ec2')
rds_client = boto3.client('rds')
cloudwatch = boto3.client('cloudwatch')
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

# Environment variables
DRY_RUN = os.environ.get('DRY_RUN', 'true').lower() == 'true'
CLEANUP_ENABLED = os.environ.get('CLEANUP_ENABLED', 'false').lower() == 'true'
CPU_THRESHOLD = float(os.environ.get('CPU_THRESHOLD', '5'))
VOLUME_AGE_DAYS = int(os.environ.get('VOLUME_AGE_DAYS', '30'))
SNAPSHOT_AGE_DAYS = int(os.environ.get('SNAPSHOT_AGE_DAYS', '90'))
S3_BUCKET = os.environ['S3_BUCKET']
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']


def lambda_handler(event, context):
    """
    Main Lambda handler for resource cleanup
    """
    try:
        print(f"Starting resource cleanup (DRY_RUN: {DRY_RUN}, ENABLED: {CLEANUP_ENABLED})")
        
        cleanup_report = {
            'timestamp': str(datetime.now()),
            'dry_run': DRY_RUN,
            'cleanup_enabled': CLEANUP_ENABLED,
            'idle_instances': [],
            'unattached_volumes': [],
            'old_snapshots': [],
            'idle_elastic_ips': [],
            'actions_taken': [],
            'estimated_savings': 0.0
        }
        
        # Find idle EC2 instances
        if CLEANUP_ENABLED:
            cleanup_report['idle_instances'] = find_idle_instances()
        
        # Find unattached EBS volumes
        cleanup_report['unattached_volumes'] = find_unattached_volumes()
        
        # Find old snapshots
        cleanup_report['old_snapshots'] = find_old_snapshots()
        
        # Find idle Elastic IPs
        cleanup_report['idle_elastic_ips'] = find_idle_elastic_ips()
        
        # Calculate estimated savings
        cleanup_report['estimated_savings'] = calculate_savings(cleanup_report)
        
        # Take cleanup actions if not in dry run mode
        if not DRY_RUN and CLEANUP_ENABLED:
            cleanup_report['actions_taken'] = perform_cleanup(cleanup_report)
        
        # Save report to S3
        save_cleanup_report(cleanup_report)
        
        # Send notification
        send_cleanup_notification(cleanup_report)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Resource cleanup completed',
                'estimated_savings': cleanup_report['estimated_savings'],
                'dry_run': DRY_RUN
            })
        }
        
    except Exception as e:
        print(f"Error in resource cleanup: {str(e)}")
        send_error_notification(str(e))
        raise


def find_idle_instances() -> List[Dict]:
    """
    Find EC2 instances with low CPU utilization
    """
    idle_instances = []
    
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )
        
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                
                # Get CPU utilization for last 7 days
                avg_cpu = get_average_cpu(instance_id, days=7)
                
                if avg_cpu < CPU_THRESHOLD:
                    idle_instances.append({
                        'instance_id': instance_id,
                        'instance_type': instance['InstanceType'],
                        'avg_cpu': avg_cpu,
                        'launch_time': str(instance['LaunchTime']),
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    })
                    print(f"Found idle instance: {instance_id} (CPU: {avg_cpu:.2f}%)")
        
    except Exception as e:
        print(f"Error finding idle instances: {str(e)}")
    
    return idle_instances


def get_average_cpu(instance_id: str, days: int = 7) -> float:
    """
    Get average CPU utilization for an EC2 instance
    """
    try:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[
                {'Name': 'InstanceId', 'Value': instance_id}
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,  # 1 day
            Statistics=['Average']
        )
        
        if response['Datapoints']:
            avg_cpu = sum(dp['Average'] for dp in response['Datapoints']) / len(response['Datapoints'])
            return avg_cpu
        
        return 0.0
        
    except Exception as e:
        print(f"Error getting CPU metrics for {instance_id}: {str(e)}")
        return 100.0  # Return high value to avoid flagging on error


def find_unattached_volumes() -> List[Dict]:
    """
    Find unattached EBS volumes older than threshold
    """
    unattached_volumes = []
    
    try:
        response = ec2_client.describe_volumes(
            Filters=[
                {'Name': 'status', 'Values': ['available']}
            ]
        )
        
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=VOLUME_AGE_DAYS)
        
        for volume in response['Volumes']:
            create_time = volume['CreateTime'].replace(tzinfo=None)
            
            if create_time < cutoff_date:
                age_days = (datetime.now().replace(tzinfo=None) - create_time).days
                
                unattached_volumes.append({
                    'volume_id': volume['VolumeId'],
                    'size': volume['Size'],
                    'volume_type': volume['VolumeType'],
                    'create_time': str(volume['CreateTime']),
                    'age_days': age_days,
                    'tags': {tag['Key']: tag['Value'] for tag in volume.get('Tags', [])}
                })
                print(f"Found unattached volume: {volume['VolumeId']} (Age: {age_days} days)")
        
    except Exception as e:
        print(f"Error finding unattached volumes: {str(e)}")
    
    return unattached_volumes


def find_old_snapshots() -> List[Dict]:
    """
    Find old EBS snapshots without tags
    """
    old_snapshots = []
    
    try:
        response = ec2_client.describe_snapshots(
            OwnerIds=['self']
        )
        
        cutoff_date = datetime.now().replace(tzinfo=None) - timedelta(days=SNAPSHOT_AGE_DAYS)
        
        for snapshot in response['Snapshots']:
            start_time = snapshot['StartTime'].replace(tzinfo=None)
            
            # Only flag snapshots without important tags and older than threshold
            has_keep_tag = any(tag['Key'].lower() == 'keep' for tag in snapshot.get('Tags', []))
            
            if start_time < cutoff_date and not has_keep_tag:
                age_days = (datetime.now().replace(tzinfo=None) - start_time).days
                
                old_snapshots.append({
                    'snapshot_id': snapshot['SnapshotId'],
                    'volume_id': snapshot.get('VolumeId', 'N/A'),
                    'size': snapshot['VolumeSize'],
                    'start_time': str(snapshot['StartTime']),
                    'age_days': age_days,
                    'description': snapshot.get('Description', '')
                })
                print(f"Found old snapshot: {snapshot['SnapshotId']} (Age: {age_days} days)")
        
    except Exception as e:
        print(f"Error finding old snapshots: {str(e)}")
    
    return old_snapshots


def find_idle_elastic_ips() -> List[Dict]:
    """
    Find unassociated Elastic IPs
    """
    idle_eips = []
    
    try:
        response = ec2_client.describe_addresses()
        
        for address in response['Addresses']:
            if 'AssociationId' not in address:
                idle_eips.append({
                    'allocation_id': address['AllocationId'],
                    'public_ip': address['PublicIp'],
                    'domain': address['Domain']
                })
                print(f"Found idle Elastic IP: {address['PublicIp']}")
        
    except Exception as e:
        print(f"Error finding idle Elastic IPs: {str(e)}")
    
    return idle_eips


def calculate_savings(report: Dict) -> float:
    """
    Calculate estimated monthly savings
    """
    savings = 0.0
    
    # EBS volume costs (approx $0.10 per GB per month for gp3)
    for volume in report['unattached_volumes']:
        savings += volume['size'] * 0.10
    
    # Snapshot costs (approx $0.05 per GB per month)
    for snapshot in report['old_snapshots']:
        savings += snapshot['size'] * 0.05
    
    # Elastic IP costs ($0.005 per hour = ~$3.60 per month)
    savings += len(report['idle_elastic_ips']) * 3.60
    
    # EC2 instance costs (estimated, varies by instance type)
    # Simple estimation: t3.micro = $7.50/month, t3.small = $15/month, etc.
    instance_cost_map = {
        't2.micro': 8.50, 't2.small': 17, 't2.medium': 34,
        't3.micro': 7.50, 't3.small': 15, 't3.medium': 30,
        't3.large': 60, 't3.xlarge': 120
    }
    
    for instance in report['idle_instances']:
        instance_type = instance['instance_type']
        savings += instance_cost_map.get(instance_type, 50)  # Default $50 if unknown
    
    return round(savings, 2)


def perform_cleanup(report: Dict) -> List[str]:
    """
    Perform actual cleanup actions
    """
    actions = []
    
    try:
        # Delete unattached volumes
        for volume in report['unattached_volumes']:
            try:
                ec2_client.delete_volume(VolumeId=volume['volume_id'])
                actions.append(f"Deleted volume: {volume['volume_id']}")
                print(f"Deleted volume: {volume['volume_id']}")
            except Exception as e:
                print(f"Error deleting volume {volume['volume_id']}: {str(e)}")
        
        # Delete old snapshots
        for snapshot in report['old_snapshots']:
            try:
                ec2_client.delete_snapshot(SnapshotId=snapshot['snapshot_id'])
                actions.append(f"Deleted snapshot: {snapshot['snapshot_id']}")
                print(f"Deleted snapshot: {snapshot['snapshot_id']}")
            except Exception as e:
                print(f"Error deleting snapshot {snapshot['snapshot_id']}: {str(e)}")
        
        # Release idle Elastic IPs
        for eip in report['idle_elastic_ips']:
            try:
                ec2_client.release_address(AllocationId=eip['allocation_id'])
                actions.append(f"Released Elastic IP: {eip['public_ip']}")
                print(f"Released Elastic IP: {eip['public_ip']}")
            except Exception as e:
                print(f"Error releasing Elastic IP {eip['public_ip']}: {str(e)}")
        
        # Stop idle instances (don't terminate by default)
        for instance in report['idle_instances']:
            try:
                ec2_client.stop_instances(InstanceIds=[instance['instance_id']])
                actions.append(f"Stopped instance: {instance['instance_id']}")
                print(f"Stopped instance: {instance['instance_id']}")
            except Exception as e:
                print(f"Error stopping instance {instance['instance_id']}: {str(e)}")
        
    except Exception as e:
        print(f"Error performing cleanup: {str(e)}")
    
    return actions


def save_cleanup_report(report: Dict):
    """
    Save cleanup report to S3
    """
    try:
        date = datetime.now()
        key = f"cleanup-reports/{date.year}/{date.month:02d}/{date.day:02d}/cleanup-report.json"
        
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=json.dumps(report, indent=2, default=str),
            ContentType='application/json'
        )
        
        print(f"Cleanup report saved to s3://{S3_BUCKET}/{key}")
        
    except Exception as e:
        print(f"Error saving cleanup report: {str(e)}")


def send_cleanup_notification(report: Dict):
    """
    Send cleanup notification via SNS
    """
    try:
        mode = "DRY RUN" if DRY_RUN else "LIVE"
        
        message = f"""
🧹 AWS Resource Cleanup Report ({mode})

💰 Estimated Monthly Savings: ${report['estimated_savings']:.2f}

📊 Resources Found:
  • Idle EC2 Instances: {len(report['idle_instances'])}
  • Unattached EBS Volumes: {len(report['unattached_volumes'])}
  • Old Snapshots: {len(report['old_snapshots'])}
  • Idle Elastic IPs: {len(report['idle_elastic_ips'])}

"""
        
        if report['actions_taken']:
            message += f"\n✅ Actions Taken ({len(report['actions_taken'])}):\n"
            for action in report['actions_taken'][:10]:  # Limit to 10 actions
                message += f"  • {action}\n"
        elif not DRY_RUN:
            message += "\n✅ No cleanup actions needed\n"
        else:
            message += "\n⚠️ Running in DRY RUN mode - no actions taken\n"
        
        message += f"\n🔍 View full report: s3://{S3_BUCKET}/cleanup-reports/"
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"AWS Resource Cleanup Report ({mode})",
            Message=message
        )
        
        print("Cleanup notification sent")
        
    except Exception as e:
        print(f"Error sending cleanup notification: {str(e)}")


def send_error_notification(error_message: str):
    """
    Send error notification
    """
    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="❌ Resource Cleanup Error",
            Message=f"Error in resource cleanup Lambda:\n\n{error_message}"
        )
    except Exception as e:
        print(f"Error sending error notification: {str(e)}")
