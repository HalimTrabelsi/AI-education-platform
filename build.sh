#!/bin/bash
set -o errexit

echo "=== Installing system dependencies ==="
apt-get update
apt-get install -y poppler-utils tesseract-ocr

echo "=== Installing Python packages ==="
pip install --upgrade pip
pip install -r requirements.txt
