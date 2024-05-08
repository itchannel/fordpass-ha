"""Fordpass API Library"""
import hashlib
import json
import logging
import os
import random
import re
import string
import time
from base64 import urlsafe_b64encode
import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from homeassistant import exceptions

_LOGGER = logging.getLogger(__name__)
defaultHeaders = {
    "Accept": "*/*",
    "Accept-Language": "en-us",
    "User-Agent": "FordPass/26 CFNetwork/1485 Darwin/23.1.0",
    "Accept-Encoding": "gzip, deflate, br",
}

loginHeaders = {
    "Accept": "*/*",
    "Accept-Language": "en-us",
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Accept-Encoding": "gzip, deflate, br",
}

apiHeaders = {
    **defaultHeaders,
    "Content-Type": "application/json",
}

region_lookup = {
    "UK&Europe": "1E8C7794-FF5F-49BC-9596-A1E0C86C5B19",
    "Australia": "5C80A6BB-CF0D-4A30-BDBF-FC804B5C1A98",
    "North America & Canada": "71A3AD0A-CF46-4CCF-B473-FC7FE5BC4592",
}

locale_lookup = {
    "UK&Europe": "EN-GB",
    "Australia": "EN-AU",
    "North America & Canada": "EN-US",
}

locale_short_lookup = {
    "UK&Europe": "GB",
    "Australia": "AUS",
    "North America & Canada": "USA",
}


NEW_API = True

BASE_URL = "https://usapi.cv.ford.com/api"
GUARD_URL = "https://api.mps.ford.com/api"
SSO_URL = "https://sso.ci.ford.com"
AUTONOMIC_URL = "https://api.autonomic.ai/v1"
AUTONOMIC_ACCOUNT_URL = "https://accounts.autonomic.ai/v1"
FORD_LOGIN_URL = "https://login.ford.com"

session = requests.Session()


class Vehicle:
    # Represents a Ford vehicle, with methods for status and issuing commands

    def __init__(
        self, username, password, vin, region, save_token=False, config_location=""
    ):
        self.username = username
        self.password = password
        self.save_token = save_token
        self.region = region_lookup[region]
        self.country_code = locale_lookup[region]
        self.short_code = locale_short_lookup[region]
        self.region2 = region
        self.vin = vin
        self.token = None
        self.expires = None
        self.expires_at = None
        self.refresh_token = None
        self.auto_token = None
        self.auto_expires_at = None
        self.errors = 0
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        if config_location == "":
            self.token_location = "custom_components/fordpass/fordpass_token.txt"
        else:
            _LOGGER.debug(config_location)
            self.token_location = config_location

    def base64_url_encode(self, data):
        """Encode string to base64"""
        return urlsafe_b64encode(data).rstrip(b'=')

    def generate_hash(self, code):
        """Generate hash for login"""
        hashengine = hashlib.sha256()
        hashengine.update(code.encode('utf-8'))
        return self.base64_url_encode(hashengine.digest()).decode('utf-8')
    
    def auth2_step1(self):
        """Auth2 step 1 obtain tokens"""
        _LOGGER.debug("Running Step1 new!")
        headers = {
            **loginHeaders,
        }
        code1 = ''.join(random.choice(string.ascii_lowercase) for i in range(43))
        code_verifier = self.generate_hash(code1)
        step1_session = requests.session()
        step1_url = f"{FORD_LOGIN_URL}/4566605f-43a7-400a-946e-89cc9fdb0bd7/B2C_1A_SignInSignUp_{self.country_code}/oauth2/v2.0/authorize?redirect_uri=fordapp://userauthorized&response_type=code&max_age=3600&scope=%2009852200-05fd-41f6-8c21-d36d3497dc64%20openid&client_id=09852200-05fd-41f6-8c21-d36d3497dc64&code_challenge={code_verifier}&code_challenge_method=S256&ui_locales={self.country_code}&language_code={self.country_code}&country_code={self.short_code}&ford_application_id=5C80A6BB-CF0D-4A30-BDBF-FC804B5C1A98"

        step1get = step1_session.get(
            step1_url,
            headers=headers,
        )

        step1get.raise_for_status()

        #_LOGGER.debug(step1_session.text)
        pattern = r'var SETTINGS = (\{[^;]*\});'
        #_LOGGER.debug(step1get.text)
        match = re.search(pattern, step1get.text)
        transId = None
        csrfToken = None
        if match:
            settings = match.group(1)
            settings_json = json.loads(settings)
            _LOGGER.debug(settings_json)
            _LOGGER.debug(settings_json["transId"])
            transId = settings_json["transId"]
            csrfToken = settings_json["csrf"]
        _LOGGER.debug(step1get.status_code)
        _LOGGER.debug(step1_session.cookies.get_dict())
        data = {
            "request_type": "RESPONSE",
            "signInName": self.username,
            "password": self.password,
        }
        urlp = f"{FORD_LOGIN_URL}/4566605f-43a7-400a-946e-89cc9fdb0bd7/B2C_1A_SignInSignUp_{self.country_code}/SelfAsserted?tx={transId}&p=B2C_1A_SignInSignUp_{self.country_code}"
        _LOGGER.debug(urlp)
        headers = {
            **loginHeaders,
            "Origin": "https://login.ford.com",
            "Referer": step1_url,
            "X-Csrf-Token": csrfToken
        }
        step1post = step1_session.post(
            urlp,
            headers=headers,
            data=data
        )
        step1post.raise_for_status()
        _LOGGER.debug("checking password")
        _LOGGER.debug(step1post.text)
        _LOGGER.debug(step1post.status_code)
        cookie_dict = step1_session.cookies.get_dict()
        _LOGGER.debug(cookie_dict)

        if step1post.status_code == 400:
            raise exceptions.HomeAssistantError(step1post.json()["message"])




        step1pt2 = step1_session.get(
            f"{FORD_LOGIN_URL}/4566605f-43a7-400a-946e-89cc9fdb0bd7/B2C_1A_SignInSignUp_{self.country_code}/api/CombinedSigninAndSignup/confirmed?rememberMe=false&csrf_token={csrfToken}",
            headers=headers,
            allow_redirects=False,
        )
        step1pt2.raise_for_status()

        test = step1pt2.headers["Location"]
        _LOGGER.debug(test)

        code_new = test.replace("fordapp://userauthorized/?code=","")

        _LOGGER.debug(code_new)

        data = {
            "client_id" : "09852200-05fd-41f6-8c21-d36d3497dc64",
            "grant_type": "authorization_code",
            "code_verifier": code1,
            "code": code_new,
            "redirect_uri": "fordapp://userauthorized"

        }

        step1pt3 = step1_session.post(
            f"{FORD_LOGIN_URL}/4566605f-43a7-400a-946e-89cc9fdb0bd7/B2C_1A_SignInSignUp_{self.country_code}/oauth2/v2.0/token",
            headers=headers,
            data=data
        )
        step1pt3.raise_for_status()

        _LOGGER.debug(step1pt3.status_code)
        _LOGGER.debug(step1pt3.text)

        tokens = step1pt3.json()
        if tokens:
            if self.auth2_step2(tokens):
                return tokens
        else:
            _LOGGER.debug("DAM IT WENT WRONG")

        







    def auth2_step2(self, result):
        _LOGGER.debug(result)

        data = {"idpToken": result["access_token"]}
        headers = {**apiHeaders, "Application-Id": self.region}
        response = session.post(
            f"{GUARD_URL}/token/v2/cat-with-b2c-access-token",
            data=json.dumps(data),
            headers=headers,
        )
        response.raise_for_status()
        _LOGGER.debug(response.status_code)
        _LOGGER.debug(response.text)
        result = response.json()
        self.token = result["access_token"]
        _LOGGER.debug(self.token)
        self.refresh_token = result["refresh_token"]
        self.expires_at = time.time() + result["expires_in"]
        _LOGGER.debug(self.expires_at)
        auto_token = self.get_auto_token()
        _LOGGER.debug("AUTO 2")
        self.auto_token = auto_token["access_token"]
        self.auto_expires_at = time.time() + result["expires_in"]
        if self.save_token:
            result["expiry_date"] = time.time() + result["expires_in"]
            result["auto_token"] = auto_token["access_token"]
            result["auto_refresh"] = "" #auto_token["refresh_token"]
            result["auto_expiry"] = time.time() + auto_token["expires_in"]

            self.write_token(result)
        session.cookies.clear()
        _LOGGER.debug("Step 5 Complete")
        return True


    def auth_step1(self):
        """Obtain data-ibm-login-url"""
        _LOGGER.debug("Running Step1")
        try:
            headers = {
                **defaultHeaders,
                'Content-Type': 'application/json',
            }
            # _LOGGER.debug("Before")
            code1 = ''.join(random.choice(string.ascii_lowercase) for i in range(43))
            code_verifier = self.generate_hash(code1)
            url1 = f"https://login.ford.com/4566605f-43a7-400a-946e-89cc9fdb0bd7/B2C_1A_SignInSignUp_{self.country_code}/oauth2/v2.0/authorize?redirect_uri=fordapp://userauthorized&response_type=code&scope=%2009852200-05fd-41f6-8c21-d36d3497dc64%20openid&max_age=3600&client_id=09852200-05fd-41f6-8c21-d36d3497dc64&code_challenge={code_verifier}&code_challenge_method=S256&ui_locales={self.country_code}&language_code={self.country_code}&country_code=AUS&ford_application_id=5C80A6BB-CF0D-4A30-BDBF-FC804B5C1A98"
            response = session.get(
                url1,
                headers=headers,
            )
            _LOGGER.debug(response.text)
            _LOGGER.debug(response.status_code)
            if response.status_code != 200:
                _LOGGER.debug("Incorrect response from URL")
                raise Exception("Response from URL was invalid")

            ibm_url = re.findall('data-ibm-login-url="(.*)"\s', response.text)[0]
            _LOGGER.debug("Step 1 Complete")
            return {"ibm_url": ibm_url, "code1": code1}
        except Exception as ex:
            _LOGGER.debug("Step 1 Exception")
            _LOGGER.debug(ex)
            return None

    def auth_step2(self, ibm_url):
        """Login using credentials"""
        _LOGGER.debug("Running Step2")
        try:
            next_url = SSO_URL + ibm_url
            headers = {
                **defaultHeaders,
                "Content-Type": "application/x-www-form-urlencoded",
            }
            data = {
                "operation": "verify",
                "login-form-type": "password",
                "username": self.username,
                "password": self.password

            }
            response = session.post(
                next_url,
                headers=headers,
                data=data,
                allow_redirects=False
            )

            if response.status_code == 302:
                next_url = response.headers["Location"]
                _LOGGER.debug("Step 2 Complete")
                return next_url
            return None
        except Exception as ex:
            _LOGGER.debug("Step 2 Exception")
            _LOGGER.debug(ex)
            if response.text is not None:
                _LOGGER.debug(response.text)
            return None

    def auth_step3(self, next_url):
        """Obtain code and grant_id"""
        _LOGGER.debug("Running Step3")
        try:

            headers = {
                **defaultHeaders,
                'Content-Type': 'application/json',
            }

            response = session.get(
                next_url,
                headers=headers,
                allow_redirects=False
            )

            if response.status_code == 302:
                next_url = response.headers["Location"]
                query = requests.utils.urlparse(next_url).query
                params = dict(x.split('=') for x in query.split('&'))
                code = params["code"]
                grant_id = params["grant_id"]
                _LOGGER.debug("Step 3 Complete")
                return {"code": code, "grant_id": grant_id}
            response.raise_for_status()
            return None

        except Exception as ex:
            _LOGGER.debug("Step 3 Exception")
            _LOGGER.debug(ex)
            if response.status_code is not None:
                _LOGGER.debug(response.status_code)
            if response.headers is not None:
                _LOGGER.debug(response.headers)
            return None

    def auth_step4(self, codes, code1):
        """Obtain access_token"""
        _LOGGER.debug("Running Step4")
        try:
            grant_id = codes["grant_id"]
            code = codes["code"]
            headers = {
                **defaultHeaders,
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {
                "client_id": "9fb503e0-715b-47e8-adfd-ad4b7770f73b",
                "grant_type": "authorization_code",
                "redirect_uri": 'fordapp://userauthorized',
                "grant_id": grant_id,
                "code": code,
                "code_verifier": code1
            }

            response = session.post(
                f"{SSO_URL}/oidc/endpoint/default/token",
                headers=headers,
                data=data

            )

            if response.status_code == 200:
                result = response.json()
                if result["access_token"]:
                    access_token = result["access_token"]
                    _LOGGER.debug("Step 4 Complete")
                    return access_token
            response.raise_for_status()
            return None
        except Exception as ex:
            _LOGGER.debug("Step 4 exception")
            _LOGGER.debug(ex)
            if response.text is not None:
                _LOGGER.debug(response.text)
            return None

    def auth_step5(self, access_token):
        """Get tokens"""
        _LOGGER.debug("Running Step5")
        try:
            data = {"ciToken": access_token}
            headers = {**apiHeaders, "Application-Id": self.region}
            response = session.post(
                f"{GUARD_URL}/token/v2/cat-with-ci-access-token",
                data=json.dumps(data),
                headers=headers,
            )

            if response.status_code == 200:
                result = response.json()

                self.token = result["access_token"]
                self.refresh_token = result["refresh_token"]
                self.expires_at = time.time() + result["expires_in"]
                auto_token = self.get_auto_token()
                self.auto_token = auto_token["access_token"]
                self.auto_expires_at = time.time() + result["expires_in"]
                if self.save_token:
                    result["expiry_date"] = time.time() + result["expires_in"]
                    result["auto_token"] = auto_token["access_token"]
                    result["auto_refresh"] = auto_token["refresh_token"]
                    result["auto_expiry"] = time.time() + auto_token["expires_in"]

                    self.write_token(result)
                session.cookies.clear()
                _LOGGER.debug("Step 5 Complete")
                return True
            response.raise_for_status()
            return False
        except Exception as ex:
            _LOGGER.debug("Step 5 exception")
            _LOGGER.debug(ex)
            if response.text is not None:
                _LOGGER.debug(response.text)
            return False

    def auth(self):
        """New Authentication System """
        _LOGGER.debug("New System")
        _LOGGER.debug(self.errors)

        # Run Step 1 auth
        access_tokens = self.auth2_step1()
        # ibm_urls = self.auth_step1()


        # if ibm_urls is None:
        #     self.errors += 1
        #     if self.errors <= 10:
        #         self.auth()
        #     else:
        #         raise Exception("Step 1 has reached error limit")

        # # Run Step 2 auth
        # login_url = self.auth_step2(ibm_urls["ibm_url"])

        # if login_url is None:
        #     self.errors += 1
        #     if self.errors <= 10:
        #         self.auth()
        #     else:
        #         raise Exception("Step 2 has reached error limit")

        # # Run Step 3 auth
        # codes = self.auth_step3(login_url)

        # if codes is None:
        #     self.errors += 1
        #     if self.errors <= 10:
        #         self.auth()
        #     else:
        #         raise Exception("Step 3 has reached error limit")

        # # Run Step 4 auth
        # access_tokens = self.auth_step4(codes, ibm_urls["code1"])

        if access_tokens is None:
            self.errors += 1
            if self.errors <= 10:
                self.auth()
            else:
                raise Exception("Step 1 has reached error limit")

        # Run Step 5 auth
        #success = self.auth_step5(access_tokens)
        success = self.auth2_step2(access_tokens)
        if success is False:
            self.errors += 1
            if self.errors <= 10:
                self.auth()
            else:
                raise Exception("Step 2 has reached error limit")
        else:
            self.errors = 0
            return True
        return False

    def refresh_token_func(self, token):
        """Refresh token if still valid"""
        _LOGGER.debug("Refreshing token")
        data = {"refresh_token": token["refresh_token"]}
        headers = {**apiHeaders, "Application-Id": self.region}

        response = session.post(
            f"{GUARD_URL}/token/v2/cat-with-refresh-token",
            data=json.dumps(data),
            headers=headers,
        )
        if response.status_code == 200:
            result = response.json()
            if self.save_token:
                result["expiry_date"] = time.time() + result["expires_in"]
                self.write_token(result)
            self.token = result["access_token"]
            self.refresh_token = result["refresh_token"]
            self.expires_at = time.time() + result["expires_in"]
        if response.status_code == 401:
            _LOGGER.debug("401 response stage 2: refresh stage 1 token")
            self.auth()

    def __acquire_token(self):
        # Fetch and refresh token as needed
        # If file exists read in token file and check it's valid
        _LOGGER.debug("Fetching token")
        if self.save_token:
            if os.path.isfile(self.token_location):
                data = self.read_token()
                self.token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.expires_at = data["expiry_date"]
                if "auto_token" in data and "auto_expiry" in data:
                    self.auto_token = data["auto_token"]
                    self.auto_expires_at = data["auto_expiry"]
                else:
                    _LOGGER.debug("AUTO token not set in file")
                    self.auto_token = None
                    self.auto_expires_at = None
            else:
                data = {}
                data["access_token"] = self.token
                data["refresh_token"] = self.refresh_token
                data["expiry_date"] = self.expires_at
                data["auto_token"] = self.auto_token
                data["auto_expiry"] = self.auto_expires_at
        else:
            data = {}
            data["access_token"] = self.token
            data["refresh_token"] = self.refresh_token
            data["expiry_date"] = self.expires_at
            data["auto_token"] = self.auto_token
            data["auto_expiry"] = self.auto_expires_at
        _LOGGER.debug(self.auto_token)
        _LOGGER.debug(self.auto_expires_at)
        if self.auto_token is None or self.auto_expires_at is None:
            self.auth()
        # self.auto_token = data["auto_token"]
        # self.auto_expires_at = data["auto_expiry"]
        if self.expires_at:
            if time.time() >= self.expires_at:
                _LOGGER.debug("No token, or has expired, requesting new token")
                self.refresh_token_func(data)
                # self.auth()
        if self.auto_expires_at:
            if time.time() >= self.auto_expires_at:
                _LOGGER.debug("Autonomic token expired")
                self.auth()
        if self.token is None:
            _LOGGER.debug("Fetching token4")
            # No existing token exists so refreshing library
            self.auth()
        else:
            _LOGGER.debug("Token is valid, continuing")

    def write_token(self, token):
        """Save token to file for reuse"""
        with open(self.token_location, "w", encoding="utf-8") as outfile:
            token["expiry_date"] = time.time() + token["expires_in"]
            _LOGGER.debug(token)
            json.dump(token, outfile)

    def read_token(self):
        """Read saved token from file"""
        try:
            with open(self.token_location, encoding="utf-8") as token_file:
                token = json.load(token_file)
                return token
        except ValueError:
            _LOGGER.debug("Fixing malformed token")
            self.auth()
            with open(self.token_location, encoding="utf-8") as token_file:
                token = json.load(token_file)
                return token

    def clear_token(self):
        """Clear tokens from config directory"""
        if os.path.isfile("/tmp/fordpass_token.txt"):
            os.remove("/tmp/fordpass_token.txt")
        if os.path.isfile("/tmp/token.txt"):
            os.remove("/tmp/token.txt")
        if os.path.isfile(self.token_location):
            os.remove(self.token_location)

    def get_auto_token(self):
        """Get token from new autonomic API"""
        _LOGGER.debug("Getting Auto Token")
        headers = {
            "accept": "*/*",
            "content-type": "application/x-www-form-urlencoded"
        }

        data = {
            "subject_token": self.token,
            "subject_issuer": "fordpass",
            "client_id": "fordpass-prod",
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",

        }

        _LOGGER.debug(data)

        r = session.post(
            f"{AUTONOMIC_ACCOUNT_URL}/auth/oidc/token",
            data=data,
            headers=headers
        )
        _LOGGER.debug(r.text)

        if r.status_code == 200:
            result = r.json()
            _LOGGER.debug(r.status_code)
            _LOGGER.debug(r.text)
            self.auto_token = result["access_token"]
            return result
        return False

    def get_status(self):
        """Get status from Autonomics endpoint"""
        params = {"lrdt": "01-01-1970 00:00:00"}

        if self.auto_token is None:
            self.__acquire_token()

        headers = {
            **apiHeaders,
            "auth-token": self.token,
            "Application-Id": self.region,
        }
        _LOGGER.debug("Status function before auto_token")
        _LOGGER.debug(self.auto_token)
        _LOGGER.debug(self.vin)

        _LOGGER.debug("Trying new vehicle API endpoint")
        headers = {
            **apiHeaders,
            "authorization": f"Bearer {self.auto_token}",
            "Application-Id": self.region,
        }
        r = session.get(
            f"{AUTONOMIC_URL}/telemetry/sources/fordpass/vehicles/{self.vin}", params=params, headers=headers
        )
        _LOGGER.debug(r.status_code)
        return r

    def status(self):
        """Get Vehicle status from API"""
        _LOGGER.debug("Getting Vehicle Status")
        self.__acquire_token()

        if NEW_API:
            r = self.get_status()
            _LOGGER.debug("NEW API???")

            if r.status_code == 200:
                #_LOGGER.debug(r.text)
                result = r.json()

                return result
            if r.status_code == 401:
                self.auth()
                response = self.get_status()
                if response.status_code == 200:
                    result = response.json()
                    return result
            if r.status_code == 403:
                i = 0
                while i < 3:
                    _LOGGER.debug(f"Retrying Vehicle endpoint attempt {i}")
                    response = self.get_status()
                    if response.status_code == 200:
                        result = response.json()
                        return result
                    i += 1
            response.raise_for_status()
        return {}

    def get_messages(self):
        """Make call to messages API"""
        headers = {
            **apiHeaders,
            "Auth-Token": self.token,
            "Application-Id": self.region,
        }
        response = session.get(f"{GUARD_URL}/messagecenter/v3/messages?", headers=headers)
        return response

    def messages(self):
        """Get Vehicle messages from API"""
        _LOGGER.debug("Getting Messages")
        self.__acquire_token()
        response = self.get_messages()
        if response.status_code == 200:
            result = response.json()
            return result["result"]["messages"]
            # _LOGGER.debug(result)
        # _LOGGER.debug(response.text)
        if response.status_code == 401:
            self.auth()
            response = self.get_messages()
            if response.status_code == 200:
                result = response.json()
                return result["result"]["messages"]
        return None

    def get_vehicles(self):
        """Make call to vehicles API"""
        _LOGGER.debug("Getting Vehicles")
        if self.region2 == "Australia":
            countryheader = "AUS"
        elif self.region2 == "North America & Canada":
            countryheader = "USA"
        elif self.region2 == "UK&Europe":
            countryheader = "GBR"
        else:
            countryheader = "USA"
        headers = {
            **apiHeaders,
            "Auth-Token": self.token,
            "Application-Id": self.region,
            "Countrycode": countryheader,
            "Locale": "EN-US"
        }

        data = {
            "dashboardRefreshRequest": "All"
        }
        response = session.post(
            f"{GUARD_URL}/expdashboard/v1/details/",
            headers=headers,
            data=json.dumps(data)
        )
        return response

    def vehicles(self):
        """Get vehicle list from account"""
        self.__acquire_token()

        response = self.get_vehicles()

        if response.status_code == 207:
            result = response.json()
            return result
        if response.status_code == 401:
            self.auth()
            response = self.get_vehicles()
            if response.status_code == 207:
                result = response.json()
                return result
        if response.status_code == 403:
            i = 0
            while i <= 3:
                response = self.get_vehicles()
                if response.status_code == 207:
                    result = response.json()
                    return result
                i += 1

        return None

    def guard_status(self):
        """Retrieve guard status from API"""
        self.__acquire_token()

        params = {"lrdt": "01-01-1970 00:00:00"}

        headers = {
            **apiHeaders,
            "auth-token": self.token,
            "Application-Id": self.region,
        }

        response = session.get(
            f"{GUARD_URL}/guardmode/v1/{self.vin}/session",
            params=params,
            headers=headers,
        )
        return response.json()

    def start(self):
        """
        Issue a start command to the engine
        """
        return self.__request_and_poll_command("remoteStart")

    def stop(self):
        """
        Issue a stop command to the engine
        """
        return self.__request_and_poll_command("cancelRemoteStart")

    def lock(self):
        """
        Issue a lock command to the doors
        """
        return self.__request_and_poll_command("lock")

    def unlock(self):
        """
        Issue an unlock command to the doors
        """
        return self.__request_and_poll_command("unlock")

    def enable_guard(self):
        """
        Enable Guard mode on supported models
        """
        self.__acquire_token()

        response = self.__make_request(
            "PUT", f"{GUARD_URL}/guardmode/v1/{self.vin}/session", None, None
        )
        _LOGGER.debug(response.text)
        return response

    def disable_guard(self):
        """
        Disable Guard mode on supported models
        """
        self.__acquire_token()
        response = self.__make_request(
            "DELETE", f"{GUARD_URL}/guardmode/v1/{self.vin}/session", None, None
        )
        _LOGGER.debug(response.text)
        return response

    def request_update(self, vin=""):
        """Send request to vehicle for update"""
        self.__acquire_token()
        if vin:
            vinnum = vin
        else:
            vinnum = self.vin
        status = self.__request_and_poll_command("statusRefresh", vinnum)
        return status

    def __make_request(self, method, url, data, params):
        """
        Make a request to the given URL, passing data/params as needed
        """

        headers = {
            **apiHeaders,
            "auth-token": self.token,
            "Application-Id": self.region,
        }

        return getattr(requests, method.lower())(
            url, headers=headers, data=data, params=params
        )

    def __request_and_poll_command(self, command, vin=None):
        """Send command to the new Command endpoint"""
        self.__acquire_token()
        headers = {
            **apiHeaders,
            "Application-Id": self.region,
            "authorization": f"Bearer {self.auto_token}"
        }

        data = {
            "properties": {},
            "tags": {},
            "type": command,
            "wakeUp": True
        }
        if vin is None:
            r = session.post(
                f"{AUTONOMIC_URL}/command/vehicles/{self.vin}/commands",
                data=json.dumps(data),
                headers=headers
            )
        else:
            r = session.post(
                f"{AUTONOMIC_URL}/command/vehicles/{self.vin}/commands",
                data=json.dumps(data),
                headers=headers
            )

        _LOGGER.debug("Testing command")
        _LOGGER.debug(r.status_code)
        _LOGGER.debug(r.text)
        if r.status_code == 201:
            # New code to hanble checking states table from vehicle data
            response = r.json()
            command_id = response["id"]
            # current_status = response["currentStatus"]
            i = 1
            while i < 14:
                # Check status every 10 seconds for 90 seconds until command completes or time expires
                status = self.status()
                _LOGGER.debug("STATUS")
                _LOGGER.debug(status)

                if "states" in status:
                    _LOGGER.debug("States located")
                    if f"{command}Command" in status["states"]:
                        _LOGGER.debug("Found command")
                        _LOGGER.debug(status["states"][f"{command}Command"]["commandId"])
                        if status["states"][f"{command}Command"]["commandId"] == command_id:
                            _LOGGER.debug("Making progress")
                            _LOGGER.debug(status["states"][f"{command}Command"])
                            if status["states"][f"{command}Command"]["value"]["toState"] == "success":
                                _LOGGER.debug("Command succeeded")
                                return True
                            if status["states"][f"{command}Command"]["value"]["toState"] == "expired":
                                _LOGGER.warning(f"Fordpass Command: {status.get('states', {}).get(f'{command}Command', {}).get('message', 'Expired Status')}")
                                if "statusRefresh" in command:
                                    raise exceptions.HomeAssistantError(f"Fordpass Command: {status.get('states', {}).get(f'{command}Command', {}).get('message', 'Expired Status')}")
                                return False
                            if status["states"][f"{command}Command"]["value"]["toState"] == "failed":
                                _LOGGER.warning(f"Fordpass Command: {status.get('states', {}).get(f'{command}Command', {}).get('message', 'Failed Status')}")
                                if "statusRefresh" in command:
                                    raise exceptions.HomeAssistantError(f"Fordpass Command: {status.get('states', {}).get(f'{command}Command', {}).get('message', 'Failed Status')}")
                                return False
                i += 1
                _LOGGER.debug("Looping again")
                time.sleep(10)
            # time.sleep(90)
            return False
        return False
