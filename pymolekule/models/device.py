"""
Device model
"""

from datetime import datetime
from pydantic import BaseModel, PrivateAttr
from typing import Optional
from loguru import logger


class DeviceModel(BaseModel):
    """Device model

    A device can be found in an account, see the `AccountModel` model

    Args:
        name (str): Name of the Molekule device
        serial_number (str): Serial number of the Molekule device
        firmware (str): Firmware number of the Molekule device
        model (str): Model of the Molekule device
        mac_address (str): MAC address of the Molekule device
        online (bool): Online status of the Molekule device
        mode (str): Protect mode of the Molekule device. Can be `smart` (which is Auto Protect in the app) or `manual`
        silent (str, optional): Quiet mode in the app, which can be found under Auto Protect > Quiet
        fan_speed (int): This is the fan speed from the manual mode only, interval:`[1,6]`
        burst (int): Not sure what it is exactly, but values are `[0, 1, 2]`
        aqi (str): Air Quality Index, values are `['good', 'moderate', 'bad', 'very_bad']`
        filter_state (int): PECO filter state. Percentage with the following interval `[0,100]`
    """

    name: str
    serial_number: str
    firmware: str
    model: str
    mac_address: str
    online: bool
    mode: str
    silent: Optional[bool] = None
    fan_speed: int
    burst: int
    aqi: str
    filter_state: Optional[int] = None


class Device(DeviceModel):
    _instance = PrivateAttr()

    def __init__(self, instance, **kwargs):
        super().__init__(**kwargs)
        self._instance = instance


    def control(self, smart: bool = 1, quiet: bool = False, fan_speed: int = None) -> Optional[dict]:
        """
        control Control device state

        :param smart: _description_, defaults to 1
        :type smart: bool, optional
        :param quiet: _description_, defaults to False
        :type quiet: bool, optional
        :param fan_speed: _description_, defaults to None
        :type fan_speed: int, optional
        :return: _description_
        :rtype: Optional[dict]
        """
        endpoint = ''
        body = {}

        try:
            if smart:
                endpoint = '/actions/enable-smart-mode'
                body = {
                    'silent': 1 if quiet is True else 0
                }
                logger.info(f"Will set '{self.name}' to Smart Mode - {'Quiet' if quiet else 'Standard'} mode")
            elif fan_speed is not None:
                endpoint = '/actions/set-fan-speed'
                body = {
                    'fanSpeed': fan_speed
                }
                logger.info(f"Will set '{self.name}' to Manual Mode - Speed {fan_speed}")
            else:
                logger.info(f"No compatible mode with smart: {smart}; quiet: {quiet}; fan_speed: {fan_speed}")
                return None

            r = self._instance.request.post(
                path=f'/users/me/devices/{self.serial_number}{endpoint}',
                json=body
            )
            r.raise_for_status()
            return r.json() if r.content else True
        except Exception as err:
            logger.err(err)
            raise err


    # WIP
    def sensor_history(self, date_start: int = None, date_end: int = None) -> Optional[dict]:
        """
        sensor_data Retrieve historical sensor data from the provided device between two dates

        :param date_start: _description_, defaults to None
        :type date_start: int, optional
        :param date_end: _description_, defaults to None
        :type date_end: int, optional
        :return: _description_
        :rtype: Optional[dict]
        """
        today = datetime.today()
        min_date = date_start if date_start else int(datetime.combine(today, datetime.min.time()).timestamp()*1000)
        max_date = date_end if date_end else int(datetime.combine(today, datetime.max.time()).timestamp()*1000)

        try:
            parameters = {
                'aggregation': False,
                'fromDate': min_date,
                'resolution': 5,
                'toDate': max_date
            }

            r = self._instance.request.get(
                path=f'/users/me/devices/{self.serial_number}/sensordata',
                params=parameters
            )

            return r.json()
            # TODO: Handle not providing `device` argument?
        except Exception as err:
            logger.error(err)
            return None
