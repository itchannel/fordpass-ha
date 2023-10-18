"""Script for grabbing vehicle JSON data from Autonomic API"""
from datetime import datetime
import glob
import json
import sys
import os
import re
import requests


# Place this script in the /config/custom_components/fordpass folder on your HomeAssistant
# Add the details below
# run from a terminal in the /config/custom_components/fordpass folder: python3 autonomicData.py
# Script will automatically redact your VIN, VehicleID, and Geolocation details (lat, long) by default, but can be turned off

# USER INPUT DATA

# Required: Enter the VIN to query
FP_VIN = ""

# Automatically redact json? (True or False) False is only recommended if you would like to save your json for personal use
REDACTION = True

# Optional: Enter your vehicle year (example: 2023)
VIC_YEAR = ""

# Optional: Enter your vehicle model (example: Lightning)
VIC_MODEL = ""

# You can turn off print statements if you want to use this script for other purposes (True or False)
VERBOSE = True


def get_autonomic_token(ford_access_token):
    """Get Autonomic API token from FordPass token"""
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
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        autonomic_token_data = response.json()
        return autonomic_token_data

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
        # print("Trying refresh token")
        # get_autonomic_token(fp_refresh)
        return None
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
    """Get vehicle status from Autonomic API"""
    base_url = "https://api.autonomic.ai/"
    endpoint = f"v1beta/telemetry/sources/fordpass/vehicles/{vin}:query"
    url = f"{base_url}{endpoint}"
    headers = {
        "Authorization": f"Bearer {access_token}",  # Replace 'your_autonom_token' with the actual Autonomic API token
        "Content-Type": "application/json",
        "accept": "*/*"
    }
    redaction_items = ["lat", "lon", "vehicleId", "vin", "latitude", "longitude"]

    try:
        response = requests.post(url, headers=headers, json={}, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad requests (4xx and 5xx status codes)

        # Parse the JSON response
        vehicle_status_data = response.json()

        # Redact sensitive information
        if REDACTION:
            redact_json(vehicle_status_data, redaction_items)
        return vehicle_status_data

    except requests.exceptions.HTTPError as errh:
        print(f"HTTP Error: {errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout Error: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Something went wrong: {err}")
    return None


def redact_json(data, redaction):
    """Redact sensitive information from JSON data"""
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
    FORD_PASS_DIR = "/config/custom_components/fordpass"
    existingfordToken = os.path.join(FORD_PASS_DIR, "*_fordpass_token.txt")
    userToken = glob.glob(existingfordToken)

    if userToken:
        for userTokenMatch in userToken:
            with open(userTokenMatch, 'r', encoding="utf-8") as file:
                fp_token_data = json.load(file)
            fpToken = fp_token_data['access_token']
            fpRefresh = fp_token_data['refresh_token']
    else:
        print(f"Error finding FordPass token text file: {existingfordToken}, {userToken}")
        sys.exit()

    if FP_VIN == "":
        print("Please enter your VIN into the python script")
        sys.exit()

    if VERBOSE:
        print("Starting")
    if REDACTION:
        REDACTION_STATUS = "_REDACTED"
        if VERBOSE:
            print("Automatically redacting json")
    else:
        REDACTION_STATUS = ""
        if VERBOSE:
            print("WARNING: json will contain sensitive information!")
    # Exchange Fordpass token for Autonomic Token
    autonomic_token = get_autonomic_token(fpToken)
    vehicle_status = get_vehicle_status(FP_VIN, autonomic_token["access_token"])
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    if VIC_YEAR != "":
        VIC_YEAR = VIC_YEAR.replace(" ", "_") + "-"
    if VIC_MODEL != "":
        VIC_MODEL = VIC_MODEL.replace(" ", "_")
    else:
        VIC_MODEL = "my"

    fileName = os.path.join(FORD_PASS_DIR, f"{VIC_YEAR}{VIC_MODEL}_status_{current_datetime}{REDACTION_STATUS}.json")

    # Write the redacted JSON data to the file
    with open(fileName, 'w', encoding="utf-8") as file:
        json.dump(vehicle_status, file, indent=4)
    if VERBOSE:
        print(f"File saved: {fileName}")
        print("Note: json file will be deleted if fordpass-ha is updated")
