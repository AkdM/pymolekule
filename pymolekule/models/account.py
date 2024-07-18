"""
Account model
"""

from .device import Device
from pydantic import BaseModel
from typing import List, Optional

class Account(BaseModel):
    """Account model

    Args:
        name (str, optional): Account holder name
        email (str, optional): Email address tied to the provided account
        devices (list, optional): List of devices, from the `Device` model
    """
    name: Optional[str] = ''
    email: Optional[str] = ''
    devices: Optional[List[Device]] = []
