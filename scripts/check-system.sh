#!/bin/bash

echo "🔍 AWS Cost Optimizer Health Check"
echo "=================================="
echo ""

REGION="us-west-2"
ACCOUNT_ID="851725642392"

# Test 1: Lambda Functions
echo "✓ Checking Lambda Functions..."
aws lambda get-function --function-name cost-optimizer-cost-monitor --region $REGION > /dev/null 2>&1 && echo "  ✓ Cost Monitor exists" || echo "  ✗ Cost Monitor missing"
aws lambda get-function --function-name cost-optimizer-resource-cleanup --region $REGION > /dev/null 2>&1 && echo "  ✓ Resource Cleanup exists" || echo "  ✗ Resource Cleanup missing"
aws lambda get-function --function-name cost-optimizer-slack-notifier --region $REGION > /dev/null 2>&1 && echo "  ✓ Slack Notifier exists" || echo "  ✗ Slack Notifier missing"

echo ""

# Test 2: S3 Buckets
echo "✓ Checking S3 Buckets..."
aws s3 ls s3://cost-optimizer-reports-$ACCOUNT_ID --region $REGION > /dev/null 2>&1 && echo "  ✓ Cost Reports bucket exists" || echo "  ✗ Cost Reports bucket missing"
aws s3 ls s3://cost-optimizer-lambda-$ACCOUNT_ID --region $REGION > /dev/null 2>&1 && echo "  ✓ Lambda deployments bucket exists" || echo "  ✗ Lambda bucket missing"

echo ""

# Test 3: EventBridge Rules
echo "✓ Checking EventBridge Schedules..."
aws events describe-rule --name cost-optimizer-daily-cost-check --region $REGION > /dev/null 2>&1 && echo "  ✓ Daily cost check scheduled" || echo "  ✗ Daily schedule missing"
aws events describe-rule --name cost-optimizer-weekly-cleanup --region $REGION > /dev/null 2>&1 && echo "  ✓ Weekly cleanup scheduled" || echo "  ✗ Weekly schedule missing"

echo ""

# Test 4: SNS Topic
echo "✓ Checking SNS Topic..."
aws sns get-topic-attributes --topic-arn "arn:aws:sns:$REGION:$ACCOUNT_ID:cost-optimizer-cost-alerts" --region $REGION > /dev/null 2>&1 && echo "  ✓ SNS topic exists" || echo "  ✗ SNS topic missing"

echo ""

# Test 5: Invoke Lambda
echo "✓ Testing Lambda Invocation..."
aws lambda invoke --function-name cost-optimizer-cost-monitor --region $REGION /tmp/test-output.json > /dev/null 2>&1
if [ $? -eq 0 ]; then
  echo "  ✓ Lambda invoked successfully"
  cat /tmp/test-output.json | jq .
else
  echo "  ✗ Lambda invocation failed"
fi

echo ""
echo "=================================="
echo "Health check complete!"
