"""
Pymolekule exceptions
"""


class PMAwsSrpAuthError(Exception):
    """
    Exception

    Exception raised when AWS SRP credentials are incorrect
    """

    def __init__(self):
        super().__init__('Unable to authenticate user for AWS SRP, check credentials')
