"""
pymolekule._account_model
~~~~~~~~~~~~~~
Account data model
"""

from dataclasses import dataclass
from typing import List
from typing import Optional

from ._device_model import Device


@dataclass
class Account:
    name: str
    email: str
    devices: Optional[List[Device]] = None
