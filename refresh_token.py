import json
import requests
from pymongo import MongoClient
import os
from datetime import datetime

# Load environment variables for multiple accounts
credentials = {
    "account1": {
        "client_id": os.getenv('AIRTHINGS_CLIENT_ID'),
        "client_secret": os.getenv('AIRTHINGS_CLIENT_SECRET')
    },
    "account2": {
        "client_id": os.getenv('AIRTHINGS_CLIENT_ID_2'),
        "client_secret": os.getenv('AIRTHINGS_CLIENT_SECRET_2')
    }
}
mongo_uri = os.getenv('MONGODB_URI')

# Connect to MongoDB
mongo_client = MongoClient(mongo_uri)
db = mongo_client['lifestyle_db']
collection = db['CustomerAirthingsData']

# Load tokens
try:
    with open('data/airthings_tokens.json', 'r') as f:
        data = json.load(f)
except Exception as e:
    print(f"Error loading airthings_tokens.json: {e}")
    raise

# Refresh tokens and fetch data for each customer
for customer in data['customers']:
    account_id = customer['accountId']
    if account_id not in credentials:
        print(f"Unknown account ID {account_id} for {customer['customerId']}")
        continue

    client_id = credentials[account_id]['client_id']
    client_secret = credentials[account_id]['client_secret']

    if not client_id or not client_secret:
        print(f"Missing client_id or client_secret for account {account_id}")
        continue

    # Refresh token
    try:
        url = "https://accounts.airthings.com/oauth/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": customer['refreshToken']
        }
        response = requests.post(url, headers=headers, data=body)
        if response.status_code == 200:
            token_data = response.json()
            customer['accessToken'] = token_data['access_token']
            customer['refreshToken'] = token_data['refresh_token']
            print(f"Token refreshed for {customer['customerId']}: {customer['accessToken']}")
        else:
            print(f"Failed to refresh token for {customer['customerId']}: {response.status_code} {response.text}")
            continue
    except Exception as e:
        print(f"Error refreshing token for {customer['customerId']}: {e}")
        continue

    # Fetch devices
    try:
        headers = {'Authorization': f'Bearer {customer["accessToken"]}'}
        device_response = requests.get('https://api.airthings.com/v1/devices', headers=headers)
        if device_response.status_code != 200:
            print(f"Failed to fetch devices for {customer['customerId']}: {device_response.text}")
            continue
        devices = device_response.json()['devices']
    except Exception as e:
        print(f"Error fetching devices for {customer['customerId']}: {e}")
        continue

    # Fetch data for each device
    for device in devices:
        try:
            data_response = requests.get(f'https://api.airthings.com/v1/devices/{device["id"]}/latest-samples', headers=headers)
            if data_response.status_code == 200:
                data = data_response.json()['data']
                record = {
                    'customerId': customer['customerId'],
                    'deviceId': device['id'],
                    'radon': data.get('radon', None),
                    'co2': data.get('co2', None),
                    'voc': data.get('voc', None),
                    'humidity': data.get('humidity', None),
                    'temperature': data.get('temp', None),
                    'recordedAt': datetime.utcnow().isoformat() + 'Z',
                    'createdAt': datetime.utcnow().isoformat() + 'Z',
                    'updatedAt': datetime.utcnow().isoformat() + 'Z'
                }
                collection.insert_one(record)
                print(f"Data stored for {customer['customerId']}, device {device['id']}")
            else:
                print(f"Failed to fetch data for device {device['id']}: {data_response.text}")
        except Exception as e:
            print(f"Error fetching data for device {device['id']}: {e}")

# Save updated tokens
try:
    with open('data/airthings_tokens.json', 'w') as f:
        json.dump(data, f, indent=2)
except Exception as e:
    print(f"Error saving airthings_tokens.json: {e}")

mongo_client.close()
