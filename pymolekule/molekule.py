"""
Main PyMolekule Molekule class that provides essential API work with AWS and Molekule servers.
"""

import sys
from typing import Optional

import boto3
from loguru import logger
from pycognito.aws_srp import AWSSRP

from ._internal_utils import (
    stealth_email,
    Request
)
from .models import Account, Device
from .exceptions import PMAwsSrpAuthError


class Molekule:
    """
    Constructor

    Main PyMolekule class that provides essential API work with AWS and Molekule servers

    Args:
        username (str, optional): The email from the provided Molekule account. If not provided along with the `password` arg, use `jwt`. Defaults to `None`
        password (str, optional): The password from the provided Molekule account. If not provided along with the `username` arg, use `jwt`. Defaults to `None`
        jwt (str, optional): Default jwt obtained after a successful login. Defaults to `None`
        pool_id (str, optional): Pool ID to use for the AWS SRP authentication. Defaults to `'us-west-2_KqrEZKC6r'`
        client_id (str, optional): Client ID to use for the AWS SRP authentication. Defaults to `'1ec4fa3oriciupg94ugoi84kkk'`
        default_region (str, optional): Default region to use for the initial AWS cognito requests. Defaults to `'us-west-2'`
        verbose (bool, optional): Verbose class output (DEBUG severity). Defaults to `False`
    """

    @logger.catch
    def __init__(
            self,
            username: str = None,
            password: str = None,
            jwt: str = None,
            pool_id: str = 'us-west-2_KqrEZKC6r',
            client_id: str = '1ec4fa3oriciupg94ugoi84kkk',
            default_region: str = 'us-west-2',
            verbose: bool = False
        ) -> None:
        severity = "INFO" if not verbose else "DEBUG"
        default_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        logger_configuration = {
            "handlers": [
                {
                    "sink": sys.stdout,
                    "level": severity,
                    "format": "{level} - <level>{message}</level>" if not verbose else default_format
                }
            ]
        }
        logger.configure(**logger_configuration)

        self.idp_client = boto3.client('cognito-idp')
        self.molekule_username = username
        self.molekule_password = password
        self.default_pool_id = pool_id
        self.app_client_id = client_id
        self.default_region = default_region
        self.tokens = {"jwt": jwt}
        self.devices = []
        self.account = Account()
        self.request = Request(self)

        self.stealth_email = stealth_email(self.molekule_username)

        pass


    @logger.catch
    def login(self) -> dict:
        logger.info(f'Trying to login with "{self.stealth_email}"')
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
            self.tokens['access_token'] = self.tokens.get('raw').get('AccessToken')
            self.tokens['id_token'] = self.tokens.get('raw').get('IdToken')

            # 2. Login to Molekule servers using previous retrieved tokens
            logger.debug('Login in to Molekule servers using previous retrieved tokens')
            molekule_auth_data = {
                "access_token": self.tokens.get('access_token'),
                "id_token": self.tokens.get('id_token'),
                "provider": f"cognito-idp.{self.default_region}.amazonaws.com/{self.default_pool_id}"
            }

            try:
                molekule_authentication = self.request.login(json=molekule_auth_data)

                molekule_authentication.raise_for_status()
                molekule_authentication_response = molekule_authentication.json()
            except Exception as err:
                raise err

            self.account.name = molekule_authentication_response.get('profile').get('name')
            self.account.email = self.molekule_username

            # Save JWT token for further use
            self.tokens['jwt'] = molekule_authentication_response.get('openIdToken')

        except Exception as err:
            logger.error(err)
            raise err

        logger.success(f'Login success')
        return dict(jwt=self.tokens["jwt"])


    @logger.catch
    def list_devices(self) -> Optional[list]:
        logger.info('Listing devices…')
        try:
            r = self.request.get('/users/me/devices')
            r.raise_for_status()
            devices = r.json().get('content', [])

            for device in devices:
                user_device = Device(
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
                    aqi=device.get('aqi'),
                    instance=self
                )
                self.devices.append(user_device)

            self.account.devices = self.devices

            if len(self.account.devices) > 0:
                print_devices = list(map(lambda d: f'{d.name} ({d.serial_number})', self.account.devices))
                logger.info(f'Found {len(self.account.devices)} device{"s" if len(self.account.devices) > 1 else ""}: {print_devices}')
            else:
                self.account.devices = None
                logger.info('No device found in provided account')
        except Exception as err:
            logger.error(err)
            return None
        return self.account.devices
