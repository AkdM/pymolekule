"""
Provides utility functions that are consumed internally by PyMolekule
"""

import re
import requests
import jwt
from loguru import logger


def stealth_email(email: str = None):
    if email:
        pattern = r"(?!^|.$)[^@]"
        s = re.search(pattern, email)
        if s:
            return re.sub(pattern, '*', email)
    return None

@logger.catch
class Request:
    def __init__(self, molekule_instance = None, verbose: bool = False) -> None:
        self.molekule_instance = molekule_instance
        self.session = requests.Session()
        pass


    def __headers(self) -> dict:
        return {
            'Authorization': self.molekule_instance.tokens['jwt'],
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Api-Version': '1.0',
            'User-Agent': 'PyMolekule'
        }


    def api_endpoint(self, path: str) -> str:
        return f'https://api.molekule.com{path}'
    

    def check_token(func):
        def wrapper(self, *args, **kwargs):
            try:
                jwt.decode(
                    self.molekule_instance.tokens['jwt'],
                    options={"verify_signature": False, "verify_exp": True}
                )
            except jwt.ExpiredSignatureError:
                logger.debug('Token has expired, generating a new one…')
                self.molekule_instance.login()


            return func(self, *args, **kwargs)

        return wrapper


    @check_token
    def get(self, path: str = None, params: dict = None):
        endpoint = self.api_endpoint(path)
        return self.session.get(
            endpoint,
            headers=self.__headers(),
            params=params
        )


    @check_token
    def post(self, path: str = None, json = None, params: dict = None):
        endpoint = self.api_endpoint(path)
        r = self.session.post(
            endpoint,
            headers=self.__headers(),
            json=json,
            params=params
        )
        return r


    def login(self, json):
        try:
            return self.session.post(
                url='https://auth.prod-env.molekule.com/',
                json=json
            )
        except Exception as err:
            raise err
