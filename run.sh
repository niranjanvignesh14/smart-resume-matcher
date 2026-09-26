#!/bin/bash
# Run: bash run.sh
set -e

if [ -z "$GEMINI_API_KEY" ]; then
  echo "GEMINI_API_KEY is not set."
  read -p "Paste your Gemini API key: " key
  export GEMINI_API_KEY="$key"
fi

echo "Installing dependencies (first run only, may take a minute)..."
pip install -r requirements.txt --quiet

echo "Starting the app..."
streamlit run app.py
