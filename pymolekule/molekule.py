"""
Main pymolekule Molekule class that provides essential API work with AWS and Molekule servers.
"""

import sys
from typing import Optional
from datetime import datetime

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
from .models import Account, Device
from .exceptions import PMAwsSrpAuthError


@logger.catch
class Molekule:
    """
    Constructor

    Main pymolekule class that provides essential API work with AWS and Molekule servers

    Args:
        username (str, optiona): The email from the provided Molekule account. If not provided along with the `password` arg, use both `api_region` and `jwt`. Defaults to `None`
        password (str, optional): The password from the provided Molekule account. If not provided along with the `username` arg, use both `api_region` and `jwt`. Defaults to `None`
        api_region (str, optional): Default api_region obtained after a successful login. To be used along `jwt` arg. Defaults to `None`
        jwt (str, optional): Default jwt obtained after a successful login. Used along `api_region` arg. Defaults to `None`
        pool_id (str, optional): Pool ID to use for the AWS SRP authentication. Defaults to `'us-west-2_KqrEZKC6r'`
        client_id (str, optional): Client ID to use for the AWS SRP authentication. Defaults to `'1ec4fa3oriciupg94ugoi84kkk'`
        default_region (str, optional): Default region to use for the initial AWS cognito requests. Defaults to `'us-west-2'`
        verbose (bool, optional): Verbose class output (DEBUG severity). Defaults to `False`
    """

    def __init__(self, username: str = None, password: str = None, api_region: str = None, jwt: str = None, pool_id: str = 'us-west-2_KqrEZKC6r', client_id: str = '1ec4fa3oriciupg94ugoi84kkk', default_region: str = 'us-west-2', verbose: bool = False) -> None:
        severity = "WARNING" if not verbose else "DEBUG"
        default_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        logger_configuration = {
            "handlers": [
                {"sink": sys.stdout, "level": severity,
                    "format": "{level} - {message}" if not verbose else default_format},
            ]
        }
        logger.configure(**logger_configuration)

        self.idp_client = boto3.client('cognito-idp')
        self.molekule_username = username
        self.molekule_password = password
        self.default_pool_id = pool_id
        self.app_client_id = client_id
        self.default_region = default_region
        self.api_region = api_region
        self.tokens = {"jwt": jwt}
        self.devices = []
        self.account = Account()

        self.stealth_email = stealth_email(self.molekule_username)

        pass

    def login(self) -> dict:
        logger.debug(f'Trying to login with "{self.stealth_email}"')
        try:
            # 1. Retrieve tokens from AWS SRP login
            logger.debug('Retrieving tokens from AWS SRP login')
            aws_srp = AWSSRP(username=self.molekule_username,
                             password=self.molekule_password,
                             pool_id=self.default_pool_id,
                             client_id=self.app_client_id,
                             client=self.idp_client)
            try:
                _tokens = aws_srp.authenticate_user()
            except Exception as err:
                raise PMAwsSrpAuthError()

            self.tokens['raw'] = _tokens.get('AuthenticationResult')
            self.tokens['access_token'] = self.tokens.get(
                'raw').get('AccessToken')
            self.tokens['id_token'] = self.tokens.get('raw').get('IdToken')

            # 2. Login to Molekule servers using previous retrieved tokens
            logger.debug(
                'Login in to Molekule servers using previous retrieved tokens')
            molekule_auth_data = {
                "access_token": self.tokens.get('access_token'),
                "id_token": self.tokens.get('id_token'),
                "provider": f"cognito-idp.{self.default_region}.amazonaws.com/{self.default_pool_id}"
            }

            try:
                molekule_authentication = requests.request(
                    method="POST",
                    url='https://auth.prod-env.molekule.com/',
                    json=molekule_auth_data
                )

                molekule_authentication.raise_for_status()
                molekule_authentication_response = molekule_authentication.json()
            except Exception as err:
                raise err

            self.account.name = molekule_authentication_response.get(
                'profile').get('name')
            self.account.email = self.molekule_username

            # Save JWT token for further use
            self.tokens['jwt'] = molekule_authentication_response.get(
                'openIdToken')
            goal_region = extract_region(
                molekule_authentication_response.get('profile').get('identityId'))
            logger.debug('JWT token retrieved')

            # 3. Make configuration from AWS using execute-api service
            logger.debug(
                'Make configuration from AWS using execute-api service')
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
            logger.debug(
                'PUT fullAccess to AWS with the informations from previous step')
            self.api_region = aws_configuration_response.get("region")

            try:
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
                raise err

        except Exception as err:
            logger.error(err)
            raise err

        logger.success(f'Login success')
        return dict(api_region=self.api_region, jwt=self.tokens["jwt"])

    def api_endpoint(self, path: str) -> str:
        return f'https://api.{self.api_region}.prod-env.molekule.com{path}'

    def __headers(self) -> dict:
        return {
            'Authorization': self.tokens['jwt'],
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Api-Version': '1.0',
            'User-Agent': 'PyMolekule'
        }

    def list_devices(self) -> Optional[list]:
        logger.debug('Listing devices…')
        endpoint = self.api_endpoint('/users/me/devices')
        try:
            r = requests.get(endpoint, headers=self.__headers())
            r.raise_for_status()
            devices = r.json().get('content', [])

            for device in devices:
                data_device = Device(
                    name=device.get('name'),
                    serial_number=device.get('serialNumber'),
                    firmware=device.get('firmwareVersion'),
                    model=device.get('model'),
                    mac_address=device.get('macAddress'),
                    online=device.get('online'),
                    mode=device.get('mode'),
                    fan_speed=int(device.get('fanspeed')),
                    burst=device.get('burst'),
                    silent=device.get('silent'),
                    filter_state=device.get('pecoFilter'),
                    aqi=device.get('aqi')
                )
                self.devices.append(data_device)

            self.account.devices = self.devices

            if len(self.account.devices) > 0:
                print_devices = list(map(
                    lambda d: f'{d.name} ({d.serial_number})', self.account.devices))
                logger.debug(
                    f'Found {len(self.account.devices)} device{"s" if len(self.account.devices) > 1 else ""}:\n{print_devices}')
            else:
                self.account.devices = None
                logger.debug('No device found in provided account')
        except Exception as err:
            logger.error(err)
            return None
        return self.account.devices

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
            r = requests.post(endpoint, headers=self.__headers(), json=body)
            r.raise_for_status()
        except Exception as err:
            logger.err(err)
            raise err

        return r.json()

    def sensor_data(self, device: str = None, date_start: int = None, date_end: int = None) -> Optional[dict]:
        """
        sensor_data Retrieve historical sensor data from the provided device between two dates

        :param device: Serial number of the device, defaults to None
        :type device: str, optional
        :param date_start: _description_, defaults to None
        :type date_start: int, optional
        :param date_end: _description_, defaults to None
        :type date_end: int, optional
        :return: _description_
        :rtype: Optional[dict]
        """
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
                    endpoint, headers=self.__headers(), params=parameters)

                return r.json()
            # TODO: Handle not providing `device` argument
        except Exception as err:
            logger.error(err)
            return None

        return None
