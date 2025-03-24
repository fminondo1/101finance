#!/bin/bash
echo "Starting Flask app with gunicorn on $PORT..."
gunicorn --bind=0.0.0.0:$PORT --timeout 600 app:app
