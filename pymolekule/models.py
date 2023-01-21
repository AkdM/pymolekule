"""
Pymolekule dataclass models
"""

import distutils

from typing import List
from typing import Optional
from dataclasses import dataclass

from ._internal_utils import Validation


@dataclass
class Device(Validation):
    """Device model

    A device can be found in an account, see the `Account` model

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
    silent: Optional[bool]
    fan_speed: int
    burst: int
    aqi: str
    filter_state: Optional[int] = None

    def validate_silent(self, value, **_) -> bool:
        if type(value) == str:
            if value == '':
                return None
            else:
                value = bool(distutils.util.strtobool(value))
        return value

    def validate_online(self, value, **_) -> bool:
        if type(value) == str:
            if value == '':
                return False
            else:
                value = bool(distutils.util.strtobool(value))
        return value

    def validate_fan_speed(self, value, **_) -> int:
        if value is None:
            return 0
        elif type(value) == str:
            return int(value)
        return value

    def validate_filter_state(self, value, **_) -> int:
        if type(value) == str:
            return int(value)
        return value


@dataclass
class Account:
    """Account model

    Args:
        name (str, optional): Account holder name
        email (str, optional): Email address tied to the provided account
        devices (list, optional): List of devices, from the `Device` model
    """
    name: Optional[str] = ''
    email: Optional[str] = ''
    devices: Optional[List[Device]] = None
