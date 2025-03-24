#!/bin/bash
echo "Starting Flask app with gunicorn on port 80..."
gunicorn --bind=0.0.0.0:80 --timeout 600 app:app
