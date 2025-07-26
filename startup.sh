#!/bin/bash

# Azure App Service startup script for Flask application
echo "=== AI Learning Tracker Azure Startup ==="
echo "Timestamp: $(date)"

# Set environment variables for production
export FLASK_ENV=production
export FLASK_DEBUG=False
export PYTHONUNBUFFERED=1

# Get port from Azure environment (default to 8000 if not set)
export PORT=${PORT:-8000}

echo "Configuration:"
echo "  Port: $PORT"
echo "  Flask environment: $FLASK_ENV"
echo "  Python path: $(which python)"
echo "  Working directory: $(pwd)"

# List files in current directory for debugging
echo "Files in current directory:"
ls -la

# Check if requirements are installed
echo "Checking Python packages..."
pip list | grep -E "(Flask|gunicorn|azure)" || echo "Some packages missing"

# Ensure database directory exists
mkdir -p ./data
chmod 755 ./data

# Test basic Python import
echo "Testing Python imports..."
python -c "import flask; print(f'Flask version: {flask.__version__}')" || {
    echo "ERROR: Flask import failed"
    exit 1
}

# Test if our app can be imported
echo "Testing application import..."
python -c "
try:
    from wsgi import application
    print('✅ Application import successful')
except Exception as e:
    print(f'❌ Application import failed: {e}')
    import traceback
    traceback.print_exc()
" || {
    echo "ERROR: Application import failed"
    # Try fallback import
    echo "Trying fallback import..."
    python -c "
try:
    from app import app
    print('✅ Fallback app import successful')
except Exception as e:
    print(f'❌ Fallback import failed: {e}')
    import traceback
    traceback.print_exc()
"
}

# Start the application with gunicorn
echo "Starting gunicorn server..."
echo "Command: gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --max-requests 1000 --max-requests-jitter 100 --access-logfile - --error-logfile - wsgi:application"

exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 300 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload \
    wsgi:application
