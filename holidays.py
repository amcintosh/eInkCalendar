from datetime import date
from typing import Optional

import requests

from settings import PROVINCE

HOLIDDAY_API_URL = "https://canada-holidays.ca/api/v1"


def get_holidays():
    response = requests.get(f"{HOLIDDAY_API_URL}/provinces/{PROVINCE}?optional=true").json()
    return response["province"]["holidays"]


def get_todays_holiday() -> Optional[str]:
    today = date.today()
    holidays = get_holidays()
    for holiday in holidays:
        if holiday["observedDate"] == today.strftime("%Y-%m-%d"):
            return holiday.get("nameEn")
    return None
