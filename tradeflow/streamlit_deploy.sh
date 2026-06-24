#!/bin/bash
# Quick deployment script for Streamlit Cloud

echo "🚀 PerfectDocAI Deployment Script"
echo "================================"
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit
fi

# Check dependencies
echo "📦 Checking dependencies..."
pip install -r requirements.txt

# Create output directory
mkdir -p output

# Run Streamlit
echo "✅ Starting Streamlit app..."
echo "🌐 Open http://localhost:8501 in your browser"
echo ""

streamlit run app.py
