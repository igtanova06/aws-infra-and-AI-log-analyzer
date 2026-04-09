#!/bin/bash

# Setup script for Bedrock Log Analyzer UI

set -e

echo "================================"
echo "Bedrock Log Analyzer UI Setup"
echo "================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $python_version"

# Create virtual environment
echo "✓ Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Verify src directory exists
echo "✓ Checking src directory..."
if [ -d "src" ]; then
    echo "  ✓ src directory found"
else
    echo "  ❌ Error: src directory not found"
    echo "  The src directory should contain the analysis modules"
    exit 1
fi

# Create .env file
echo "✓ Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✓ .env created from .env.example"
    echo "  ⚠ Please update .env with your AWS credentials"
else
    echo "  ✓ .env already exists"
fi

# Check AWS CLI
echo "✓ Checking AWS CLI..."
if command -v aws &> /dev/null; then
    aws_version=$(aws --version)
    echo "  ✓ AWS CLI found: $aws_version"
else
    echo "  ⚠ AWS CLI not found. Please install it:"
    echo "  https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
fi

# Check AWS credentials
echo "✓ Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo "  ✓ AWS credentials configured"
else
    echo "  ⚠ AWS credentials not configured"
    echo "  Please run: aws configure"
fi

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Update .env with your AWS configuration"
echo "2. Run: source venv/bin/activate"
echo "3. Run: streamlit run streamlit_app.py"
echo ""
