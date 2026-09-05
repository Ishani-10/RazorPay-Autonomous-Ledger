#!/bin/bash
# Initialize and run The Autonomous Ledger

# Ensure we are in the correct directory
cd "$(dirname "$0")"

# Load environment variables if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
fi

# Install dependencies silently
pip install -r requirements.txt > /dev/null 2>&1

# Run the Streamlit UI
streamlit run ui/dashboard.py --server.port 8501 --server.address 0.0.0.0
