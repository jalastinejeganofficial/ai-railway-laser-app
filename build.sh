#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Starting build process..."

# Upgrade pip to latest version
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Verify critical packages
echo "✅ Verifying installation..."
python -c "import flask; import gunicorn; import supabase; print('All critical packages installed successfully!')"

# Run startup validation checks
echo "🔍 Running startup validation..."
python startup.py

echo "✅ Build completed successfully!"