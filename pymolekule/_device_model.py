"""
pymolekule._device_model
~~~~~~~~~~~~~~
Device data model
"""

import distutils

from dataclasses import dataclass
from typing import Optional

from ._internal_utils import Validation


@dataclass
class Device(Validation):
    name: str
    serial_number: str
    firmware: str
    model: str
    mac_address: str
    online: bool
    mode: str
    fan_speed: int
    burst: int
    aqi: str
    silent: Optional[bool]
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
