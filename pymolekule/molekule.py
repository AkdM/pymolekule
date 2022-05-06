"""
pymolekule.Molekule
~~~~~~~~~~~~~~
Main pymolekule Mokekule class that provides essential API work
with AWS and Molekule servers
"""

import requests
import boto3
from pycognito.aws_srp import AWSSRP

from ._internal_utils import make_configuration, create_access


class Molekule:

    def __init__(self, username: str, password: str, pool_id: str, client_id: str, default_region: str = 'us-west-2') -> None:
        self.idp_client = boto3.client('cognito-idp')
        self.molekule_username = username
        self.molekule_password = password
        self.default_pool_id = pool_id
        self.app_client_id = client_id
        self.default_region = default_region
        self.api_region = None
        self.tokens = {}

        pass

    def login(self):
        try:
            # 1. Retrieve tokens from AWS SRP login
            aws_srp = AWSSRP(username=self.molekule_username,
                             password=self.molekule_password,
                             pool_id=self.default_pool_id,
                             client_id=self.app_client_id,
                             client=self.idp_client)
            _tokens = aws_srp.authenticate_user()
            self.tokens['raw'] = _tokens.get('AuthenticationResult')
            self.tokens['access_token'] = self.tokens.get(
                'raw').get('AccessToken')
            self.tokens['id_token'] = self.tokens.get('raw').get('IdToken')

            # 2. Login to Molekule servers using previous retrieved tokens
            molekule_auth_data = {
                "access_token": self.tokens.get('access_token'),
                "id_token": self.tokens.get('id_token'),
                "provider": f"cognito-idp.{self.default_region}.amazonaws.com/{self.default_pool_id}"
            }

            molekule_authentication = requests.request(
                method="POST",
                url='https://auth.prod-env.molekule.com/',
                json=molekule_auth_data
            )

            molekule_authentication.raise_for_status()
            molekule_authentication_response = molekule_authentication.json()

            # Save JWT token for further use
            self.tokens['jwt'] = molekule_authentication_response.get(
                'openIdToken')

            # 3. Make configuration from AWS using execute-api service
            aws_configuration = make_configuration(
                endpoint='https://config.prod-env.molekule.com/',
                security_token=molekule_authentication_response.get(
                    'credentials').get('SessionToken'),
                aws_access_key_id=molekule_authentication_response.get(
                    'credentials').get('AccessKeyId'),
                aws_secret_key=molekule_authentication_response.get(
                    'credentials').get('SecretKey'),
                goal_region="us-east-1"
            )

            aws_configuration_response = aws_configuration.json()
            # 4. PUT fullAccess to AWS with the informations from step 3.
            self.api_region = aws_configuration_response.get("region")

            create_access(
                endpoint=f'https://iot.{self.api_region}.amazonaws.com/principal-policies/fullAccess',
                security_token=molekule_authentication_response.get(
                    'credentials').get('SessionToken'),
                aws_access_key_id=molekule_authentication_response.get(
                    'credentials').get('AccessKeyId'),
                aws_secret_key=molekule_authentication_response.get(
                    'credentials').get('SecretKey'),
                goal_region=aws_configuration_response.get('region'),
                amzn_iot=aws_configuration_response.get('identity_pool')
            )

        except requests.exceptions.RequestException as err:
            print("Error:", err)
            return False
        return True

    def api_endpoint(self, path: str):
        return f'https://api.{self.api_region}.prod-env.molekule.com{path}'

    def headers(self):
        return {
            'Authorization': self.tokens['jwt'],
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Api-Version': '1.0',
            'User-Agent': 'Molekule/4.1 (com.molekule.ios; build:1286; iOS 15.4.1) Alamofire/4.1'
        }

    def list_devices(self):
        endpoint = self.api_endpoint('/users/me/devices')
        req = requests.get(endpoint, headers=self.headers())
        if req.status_code == 200:
            self.devices = req.json().get('content')

            print('Found devices:')
            for device in self.devices:
                print('\n######')
                print(f'name: {device.get("name")}')
                print(f'model: {device.get("model")}')
                print(f'fw: {device.get("firmwareVersion")}')
                print(f'mac: {device.get("macAddress")}')
                print(f'sn: {device.get("serialNumber")}')
                print(
                    f'status: {"online" if device.get("online") else "offline"}')
        return req

    def control_mode(self, device: str, smart: bool = 1, quiet: bool = False, fan_speed: int = None):
        endpoint = ''
        body = {}

        if smart:
            endpoint = '/actions/enable-smart-mode'
            body = {
                'silent': 1 if quiet is True else 0
            }
            print(
                f"Will set to Smart Mode - {'Quiet' if quiet else 'Standard'} mode")
        elif fan_speed is not None:
            endpoint = '/actions/set-fan-speed'
            body = {
                'fanSpeed': fan_speed
            }
            print(
                f"Will set to Manual Mode - Speed {fan_speed}")
        else:
            print("None set")
            return

        endpoint = self.api_endpoint(f'/users/me/devices/{device}{endpoint}')
        return requests.post(endpoint, headers=self.headers(), json=body)

    def sensor_data(self, device: str):
        # TODO
        parameters = {
            'aggregation': False,
            'fromDate': 1651528800000,
            'resolution': 5,
            'toDate': 1651615199000
        }
        endpoint = self.api_endpoint(f'/users/me/devices/{device}/sensordata')
        return requests.get(endpoint, headers=self.headers(), params=parameters)

    def check_availability(self):
        return requests.get(self.api_endpoint('/feature/subscriptions/actions/check-availability'), headers=self.headers())
