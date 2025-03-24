#!/bin/bash
source /tmp/8dd6a735c752dff/antenv/bin/activate
echo "Starting Flask app with gunicorn on $PORT..."
gunicorn --bind=0.0.0.0:$PORT --timeout 600 app:app
