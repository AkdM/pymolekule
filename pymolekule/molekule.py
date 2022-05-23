"""
pymolekule.molekule
~~~~~~~~~~~~~~
Main pymolekule Molekule class that provides essential API work
with AWS and Molekule servers
"""

from typing import Optional
from datetime import datetime

import sys
import requests
import boto3
from loguru import logger
from pycognito.aws_srp import AWSSRP

from ._internal_utils import (
    make_configuration,
    create_access,
    stealth_email,
    extract_region
)


@logger.catch
class Molekule:

    def __init__(self, username: str, password: str, pool_id: str, client_id: str, default_region: str = 'us-west-2', verbose=False) -> None:
        severity = "WARNING" if not verbose else "DEBUG"
        logger_configuration = {
            "handlers": [
                {"sink": sys.stdout, "level": severity},
            ]
        }
        logger.configure(**logger_configuration)

        self.idp_client = boto3.client('cognito-idp')
        self.molekule_username = username
        self.molekule_password = password
        self.default_pool_id = pool_id
        self.app_client_id = client_id
        self.default_region = default_region
        self.api_region = None
        self.tokens = {}
        self.devices = None

        self.stealth_email = stealth_email(self.molekule_username)

        pass

    def login(self) -> bool:
        logger.debug(f'Trying to login with "{self.stealth_email}"')
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
            goal_region = extract_region(
                molekule_authentication_response.get('profile').get('identityId'))

            # 3. Make configuration from AWS using execute-api service
            aws_configuration = make_configuration(
                endpoint='https://config.prod-env.molekule.com/',
                security_token=molekule_authentication_response.get(
                    'credentials').get('SessionToken'),
                aws_access_key_id=molekule_authentication_response.get(
                    'credentials').get('AccessKeyId'),
                aws_secret_key=molekule_authentication_response.get(
                    'credentials').get('SecretKey'),
                goal_region=goal_region
            )
            aws_configuration.raise_for_status()

            aws_configuration_response = aws_configuration.json()
            # 4. PUT fullAccess to AWS with the informations from step 3.
            self.api_region = aws_configuration_response.get("region")

            create_access_request = create_access(
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
            create_access_request.raise_for_status()

        except Exception as err:
            logger.error(err)
            raise err

        logger.success(f'Login success')
        return True

    def api_endpoint(self, path: str) -> str:
        return f'https://api.{self.api_region}.prod-env.molekule.com{path}'

    def headers(self) -> dict:
        return {
            'Authorization': self.tokens['jwt'],
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Api-Version': '1.0',
            'User-Agent': 'Molekule/4.1 (com.molekule.ios; build:1286; iOS 15.4.1) Alamofire/4.1'
        }

    def list_devices(self) -> Optional[list]:
        logger.debug('Listing devices…')
        endpoint = self.api_endpoint('/users/me/devices')
        try:
            r = requests.get(endpoint, headers=self.headers())
            r.raise_for_status()
            self.devices = r.json().get('content', [])

            if len(self.devices) > 0:
                print_devices = list(map(
                    lambda d: f'{d.get("name")} ({d.get("serialNumber")})', self.devices))
                logger.debug(
                    f'Found {len(self.devices)} device{"s" if len(self.devices) > 1 else ""}:\n{print_devices}')
            else:
                self.devices = None
                logger.debug('No device found in provided account')
        except Exception as err:
            logger.error(err)
            return None
        return self.devices

    def control_mode(self, device: str, smart: bool = 1, quiet: bool = False, fan_speed: int = None) -> Optional[dict]:
        endpoint = ''
        body = {}

        try:

            if smart:
                endpoint = '/actions/enable-smart-mode'
                body = {
                    'silent': 1 if quiet is True else 0
                }
                logger.debug(
                    f"Will set to Smart Mode - {'Quiet' if quiet else 'Standard'} mode")
            elif fan_speed is not None:
                endpoint = '/actions/set-fan-speed'
                body = {
                    'fanSpeed': fan_speed
                }
                logger.debug(f"Will set to Manual Mode - Speed {fan_speed}")
            else:
                logger.debug(
                    f"No compatible mode with smart: {smart}; quiet: {quiet}; fan_speed: {fan_speed}")
                return None

            endpoint = self.api_endpoint(
                f'/users/me/devices/{device}{endpoint}'
            )
            r = requests.post(endpoint, headers=self.headers(), json=body)
            r.raise_for_status()
        except Exception as err:
            logger.err(err)
            raise err

        return r.json()

    def sensor_data(self, device: str = None, date_start: int = None, date_end: int = None) -> Optional[dict]:
        today = datetime.today()
        min_date = date_start if date_start else int(datetime.combine(
            today, datetime.min.time()).timestamp()*1000)
        max_date = date_end if date_end else int(datetime.combine(
            today, datetime.max.time()).timestamp()*1000)

        try:
            if device is not None:
                parameters = {
                    'aggregation': False,
                    'fromDate': min_date,
                    'resolution': 5,
                    'toDate': max_date
                }
                endpoint = self.api_endpoint(
                    f'/users/me/devices/{device}/sensordata')
                r = requests.get(
                    endpoint, headers=self.headers(), params=parameters)

                return r.json()
        except Exception as err:
            logger.error(err)
            return None

        return None
