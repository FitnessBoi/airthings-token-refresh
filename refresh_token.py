import requests
import json
import os

# Airthings API credentials (stored as GitHub Secrets)
client_id = os.getenv("AIRTHINGS_CLIENT_ID")
client_secret = os.getenv("AIRTHINGS_CLIENT_SECRET")

def fetch_airthings_token():
    if not client_id or not client_secret:
        raise Exception("Missing AIRTHINGS_CLIENT_ID or AIRTHINGS_CLIENT_SECRET environment variables")
    url = "https://accounts-api.airthings.com/v1/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = f"grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}"
    response = requests.post(url, headers=headers, data=body)
    if response.status_code == 200:
        token_data = response.json()
        return token_data["access_token"]
    else:
        raise Exception(f"Failed to fetch token: {response.status_code} {response.text}")

if __name__ == "__main__":
    try:
        token = fetch_airthings_token()
        # Save the token to a file in the repository
        with open("airthings_token.json", "w") as f:
            json.dump({"access_token": token}, f)
        print(f"Token refreshed: {token}")
    except Exception as e:
        print(f"Error: {e}")
        # Create a dummy file to indicate failure (for debugging)
        with open("airthings_token.json", "w") as f:
            json.dump({"error": str(e)}, f)
