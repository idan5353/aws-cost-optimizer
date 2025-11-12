#!/bin/bash

# Script to package Lambda functions

set -e

echo "Packaging Lambda functions..."

# Create builds directory
mkdir -p builds

# Package cost_monitor
echo "Packaging cost_monitor..."
cd lambda/cost_monitor
pip install -r requirements.txt -t .
zip -r ../../builds/cost_monitor.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

# Package resource_cleanup
echo "Packaging resource_cleanup..."
cd lambda/resource_cleanup
pip install -r requirements.txt -t .
zip -r ../../builds/resource_cleanup.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

# Package slack_notifier
echo "Packaging slack_notifier..."
cd lambda/slack_notifier
pip install -r requirements.txt -t .
zip -r ../../builds/slack_notifier.zip . -x "*.pyc" -x "__pycache__/*"
cd ../..

echo "✅ All Lambda functions packaged successfully!"
