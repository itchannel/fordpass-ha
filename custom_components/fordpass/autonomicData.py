import json
import requests
import sys
import os
import re
from datetime import datetime


# Place this script in the /config/custom_components/fordpass folder on your HomeAssistant
# Add the details below
# run from a terminal in the /config/custom_components/fordpass folder: python3 autonomicData.py
# It will create username_status_timestamp.json in the same folder
# Script will automatically redact your VIN, VehicleID, and Geolocation details (lat, long)

#GitHub username to append to the filename
gitHub_username = ""
#FordPass VIN for vehicle to get data from
fp_vin = "" 
#Name of the file for the user_fordpass_token.txt from the fordpass-ha integration
fp_token = "_fordpass_token.txt"

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
        print(f"Trying refresh token")
        get_autonomic_token(ford_refresh_token)
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
        sys.exit()
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
        sys.exit()
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")
        sys.exit()


def get_vehicle_status(vin, access_token):
    BASE_URL = "https://api.autonomic.ai/"
    endpoint = f"v1beta/telemetry/sources/fordpass/vehicles/{vin}:query"
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",  # Replace 'your_autonom_token' with the actual Autonomic API token
        "Content-Type": "application/json",
        "accept": "*/*"
    }
    redactionItems = ["lat", "lon", "vehicleId", "vin", "latitude", "longitude"]

    try:
        response = requests.post(url, headers=headers, json={})
        response.raise_for_status()  # Raise HTTPError for bad requests (4xx and 5xx status codes)

        # Parse the JSON response
        vehicle_status_data = response.json()

        # Redact sensitive information
        redact_json(vehicle_status_data, redactionItems)
        return vehicle_status_data

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")

def redact_json(data, redaction):
    # Regular expression to match GPS coordinates
    gps_pattern = r'"gpsDegree":\s*-?\d+\.\d+,\s*"gpsFraction":\s*-?\d+\.\d+,\s*"gpsSign":\s*-?\d+\.\d+'

    if isinstance(data, dict):
        for key in list(data.keys()):
            if key in redaction:
                data[key] = 'REDACTED'
            else:
                if isinstance(data[key], str):
                    # Redact GPS coordinates in string values
                    data[key] = re.sub(gps_pattern, '"gpsDegree": "REDACTED", "gpsFraction": "REDACTED", "gpsSign": "REDACTED"', data[key])
                else:
                    redact_json(data[key], redaction)
            # Special handling for 'stringArrayValue'
            if key == 'stringArrayValue':
                for i in range(len(data[key])):
                    data[key][i] = re.sub(gps_pattern, '"gpsDegree": "REDACTED", "gpsFraction": "REDACTED", "gpsSign": "REDACTED"', data[key][i])
    elif isinstance(data, list):
        for item in data:
            redact_json(item, redaction)
       
            
if __name__ == "__main__":
    workingDir = "/config/custom_components/fordpass"
    if gitHub_username == "":
        gitHub_username = 'my'
    if fp_vin == "":
        print("Please enter your VIN into the python script")
        sys.exit()
    if fp_token == "":
        print("Please enter your FordPass token text file name into the python script")
        sys.exit()
    elif os.path.isfile(os.path.join(workingDir, fp_token)) == False:
        print(f"Error finding FordPass token text file: {os.path.join(workingDir, fp_token)}")
        sys.exit()

    fp_token = os.path.join(workingDir, fp_token)
    # Get FordPass token
    with open(fp_token, 'r') as file:
        fp_token_data = json.load(file)

    ford_access_token = fp_token_data['access_token']
    ford_refresh_token = fp_token_data['refresh_token']
    # Exchange Fordpass token for Autonomic Token
    autonomic_token = get_autonomic_token(ford_access_token)
    vehicle_status = get_vehicle_status(fp_vin, autonomic_token["access_token"])

    current_datetime = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    fileName = os.path.join(workingDir, f"{gitHub_username}_status_{current_datetime}.json")

    # Write the updated JSON data to the file
    with open(fileName, 'w') as file:
        json.dump(vehicle_status, file, indent=4)
    print("done")