import requests
import logging
import time
import json
import os.path

defaultHeaders = {
    'Accept': '*/*',
    'Accept-Language': 'en-us',
    'User-Agent': 'fordpass-ap/93 CFNetwork/1197 Darwin/20.0.0',
    'Accept-Encoding': 'gzip, deflate, br',
}

apiHeaders = {
    **defaultHeaders,
    'Application-Id': '5C80A6BB-CF0D-4A30-BDBF-FC804B5C1A98',
    'Content-Type': 'application/json',
}

baseUrl = 'https://usapi.cv.ford.com/api'

class Vehicle(object):
    #Represents a Ford vehicle, with methods for status and issuing commands

    def __init__(self, username, password, vin, saveToken=False):
        self.username = username
        self.password = password
        self.saveToken = saveToken
        self.vin = vin
        self.token = None
        self.expires = None
        self.expiresAt = None
        self.refresh_token = None
    def auth(self):
        '''Authenticate and store the token'''

        data = {
            'client_id': '9fb503e0-715b-47e8-adfd-ad4b7770f73b',
            'grant_type': 'password',
            'username': self.username,
            'password': self.password
        }

        headers = {
            **defaultHeaders,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        # Fetch OAUTH token stage 1 
        r = requests.post('https://sso.ci.ford.com/oidc/endpoint/default/token', data=data, headers=headers)

        if r.status_code == 200:
            logging.info('Succesfully fetched token Stage1')
            result = r.json()
            data = {
             "code": result["access_token"]
            }
            headers = {
              **apiHeaders
            }
            #Fetch OAUTH token stage 2 and refresh token
            r = requests.put('https://api.mps.ford.com/api/oauth2/v1/token', data=json.dumps(data), headers=headers)
            if r.status_code == 200:
               result = r.json()
               self.token = result['access_token']
               self.refresh_token = result["refresh_token"]
               self.expiresAt = time.time() + result['expires_in']
               if self.saveToken:
                   result["expiry_date"] = time.time() + result['expires_in']
                   self.writeToken(result)
               return True
        else:
            r.raise_for_status()


    def refreshToken(self, token):
        #Token is invalid so let's try refreshing it
        data = {
             "refresh_token": token["refresh_token"]
               }
        headers = {
            **apiHeaders
        }

        r = requests.put('https://api.mps.ford.com/api/oauth2/v1/refresh', data=json.dumps(data), headers=headers)
        if r.status_code == 200:
            result = r.json()
            if self.saveToken:
                result["expiry_date"] = time.time() + result['expires_in']
                self.writeToken(result)
            self.token = result['access_token']
            self.refreshToken = result["refresh_token"]
            self.expiresAt = time.time() + result['expires_in']

    def __acquireToken(self):
        #Fetch and refresh token as needed
        #If file exists read in token file and check it's valid
        if self.saveToken:
            if os.path.isfile('/tmp/token.txt'):
                data = self.readToken()
            else:
                data = dict()
                data["access_token"] = self.token
                data["refresh_token"] = self.refresh_token
                data["expiry_date"] = self.expiresAt
        else:
            data = dict()
            data["access_token"] = self.token
            data["refresh_token"] = self.refresh_token
            data["expiry_date"] = self.expiresAt
        self.token=data["access_token"]
        self.expiresAt = data["expiry_date"]
        if self.expiresAt:
            if time.time() >= self.expiresAt:
               logging.info('No token, or has expired, requesting new token')
               self.refreshToken(data)
               #self.auth()
        if self.token == None:
            #No existing token exists so refreshing library
            self.auth()
        else:
            logging.info('Token is valid, continuing')
            pass

    def writeToken(self, token):
        #Save token to file to be reused
        with open('/tmp/token.txt', 'w') as outfile:
            token["expiry_date"] = time.time() + token['expires_in']
            json.dump(token, outfile)

    def readToken(self):
        #Get saved token from file
        with open('/tmp/token.txt') as token_file:
            return json.load(token_file)

    def status(self):
        #Get the status of the vehicle

        self.__acquireToken()

        params = {
            'lrdt': '01-01-1970 00:00:00'
        }

        headers = {
            **apiHeaders,
            'auth-token': self.token
        }

        r = requests.get(f'{baseUrl}/vehicles/v4/{self.vin}/status', params=params, headers=headers)
        if r.status_code == 200:
            result = r.json()
            if result["status"] == 402:
               r.raise_for_status()
            return result['vehiclestatus']
        else:
            r.raise_for_status()

    def start(self):
        '''
        Issue a start command to the engine
        '''
        return self.__requestAndPoll('PUT', f'{baseUrl}/vehicles/v2/{self.vin}/engine/start')

    def stop(self):
        '''
        Issue a stop command to the engine
        '''
        return self.__requestAndPoll('DELETE', f'{baseUrl}/vehicles/v2/{self.vin}/engine/start')


    def lock(self):
        '''
        Issue a lock command to the doors
        '''
        return self.__requestAndPoll('PUT', f'{baseUrl}/vehicles/v2/{self.vin}/doors/lock')


    def unlock(self):
        '''
        Issue an unlock command to the doors
        '''
        return self.__requestAndPoll('DELETE', f'{baseUrl}/vehicles/v2/{self.vin}/doors/lock')

    def requestUpdate(self):
        #Send request to refresh data from the cars module
        self.__acquireToken()
        status = self.__makeRequest('PUT', f'{baseUrl}/vehicles/v2/{self.vin}/status', None, None)
        return status.json()["status"]


    def __makeRequest(self, method, url, data, params):
        '''
        Make a request to the given URL, passing data/params as needed
        '''

        headers = {
            **apiHeaders,
            'auth-token': self.token
        }

        return getattr(requests, method.lower())(url, headers=headers, data=data, params=params)

    def __pollStatus(self, url, id):
        '''
        Poll the given URL with the given command ID until the command is completed
        '''
        status = self.__makeRequest('GET', f'{url}/{id}', None, None)
        result = status.json()
        if result['status'] == 552:
            logging.info('Command is pending')
            time.sleep(5)
            return self.__pollStatus(url, id) # retry after 5s
        elif result['status'] == 200:
            logging.info('Command completed succesfully')
            return True
        else:
            logging.info('Command failed')
            return False

    def __requestAndPoll(self, method, url):
        self.__acquireToken()
        command = self.__makeRequest(method, url, None, None)

        if command.status_code == 200:
            result = command.json()
            return self.__pollStatus(url, result['commandId'])
        else:
            command.raise_for_status()