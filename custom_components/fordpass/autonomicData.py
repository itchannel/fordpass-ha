import json
import requests

# Place this script in the /config/custom_components/fordpass folder on your HomeAssistant
# Add the details below
# run from a terminal: python3 autonomicData.py
# It will create autonomicData.json in the same folder

#FordPass Username
fp_username = "" 
#FordPass password
fp_password = "" 
#FordPass VIN for vehicle to get data from
fp_vin = "" 
#Name of the file for the user_fordpass_token.txt from the fordpass-ha integration
fp_token = "Hass_fordpass_token.txt" 


def get_autonomic_token(ford_access_token):
    url = "https://accounts.autonomic.ai/v1/auth/oidc/token"
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded"
    }
    data = {
        "subject_token": ford_access_token,
        "subject_issuer": "fordpass",
        "client_id": "fordpass-prod",
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt"
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        autonomic_token_data = response.json()
        return autonomic_token_data

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")

def get_vehicle_status(vin, access_token):
    BASE_URL = "https://api.autonomic.ai/"
    endpoint = f"v1beta/telemetry/sources/fordpass/vehicles/{vin}:query"
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",  # Replace 'your_autonom_token' with the actual Autonomic API token
        "Content-Type": "application/json",
        "accept": "*/*"
    }

    try:
        response = requests.post(url, headers=headers, json={})
        response.raise_for_status()  # Raise HTTPError for bad requests (4xx and 5xx status codes)

        # Parse the JSON response
        vehicle_status_data = response.json()
        return vehicle_status_data

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")

# Get FordPass token
with open(fp_token, 'r') as file:
    fp_token_data = json.load(file)

ford_access_token = fp_token_data['access_token']

# Exchange Fordpass token for Autonomic Token
autonomic_token = get_autonomic_token(ford_access_token)
vehicle_status = get_vehicle_status(fp_vin, autonomic_token["access_token"])

# Write the updated JSON data to the file
with open('autonomicData.json', 'w') as file:
    json.dump(vehicle_status, file, indent=4)
print("done")

