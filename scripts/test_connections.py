import sys
import os
import requests
from pymongo import MongoClient

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import MONGO_URI, AZURE_APP_SERVICE

def test_database_connection():
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database()
        print(f"Connected to MongoDB database: {db.name}")
        client.close()
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")

def test_app_service_connection():
    try:
        url = f"https://{AZURE_APP_SERVICE['default_domain']}"
        response = requests.get(url)
        if response.status_code == 200:
            print(f"Successfully connected to Azure App Service: {url}")
        else:
            print(f"Failed to connect to Azure App Service. Status code: {response.status_code}")
            print(f"Response content: {response.text}")
    except Exception as e:
        print(f"Error connecting to Azure App Service: {e}")

if __name__ == "__main__":
    print("Testing database connection...")
    test_database_connection()
    print("\nTesting Azure App Service connection...")
    test_app_service_connection()
