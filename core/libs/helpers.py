import random
import string
from datetime import datetime
import json  # Import the json module

TIMESTAMP_WITH_TIMEZONE_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'


class GeneralObject:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_utc_now():
    return datetime.utcnow()

def get_json_from_header(header_value):
    """
    Extracts and returns JSON data from the specified header value.
    Expects the header_value to be a JSON string.
    """
    try:
        return json.loads(header_value)
    except ValueError:
        raise ValueError("Invalid JSON format in header.")

