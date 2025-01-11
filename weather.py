import logging
import os
from dataclasses import dataclass

import requests
from PIL import Image
from PIL.Image import Image as TImage

from settings import OPENWEATHERMAP_API_KEY, WEATHER_CITY

logger = logging.getLogger('app')

CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
WEATHER_PICTURES_PATH = os.path.join(CURRENT_PATH, 'pictures', 'weather')

BASE_URL = "https://api.openweathermap.org"
CITY_LIMIT = 5


@dataclass
class Weather:
    temp: int
    feels_like: int
    temp_min: int
    temp_max: int
    weather: str
    weather_desc: str
    weather_icon: Image
    rain: int
    snow: int
    clouds: int


def get_lat_long():
    geo_url = f"{BASE_URL}/geo/1.0/direct?q={WEATHER_CITY}&limit={CITY_LIMIT}&appid={OPENWEATHERMAP_API_KEY}"
    try:
        data = requests.get(geo_url).json()
        return data[0].get("lat"), data[0].get("lon")
    except Exception as e:
        logger.error("Failed to fetch city location", e)
        return None, None


def get_weather_icon(icon: str) -> TImage:
    image = Image.open(os.path.join(WEATHER_PICTURES_PATH, f"{icon}.png"))
    return image.resize((100, 100)).convert("1")


def get_weather():
    lat, lon = get_lat_long()
    if not lat or not lon:
        return None
    weather_url = f"{BASE_URL}/data/3.0/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,alerts&units=metric&appid={OPENWEATHERMAP_API_KEY}"
    try:
        data = requests.get(weather_url).json()

        current = data["current"]
        today = data["daily"][0]
        weather = Weather(
            temp=round(current["temp"]),
            feels_like=round(current["feels_like"]),
            temp_min=round(today["temp"]["min"]),
            temp_max=round(today["temp"]["max"]),
            weather=today["weather"][0]["main"],
            weather_desc=today["weather"][0]["description"],
            weather_icon=get_weather_icon(today["weather"][0]["icon"][:2]),
            rain=round(today.get("rain", 0)),
            snow=round(today.get("snow", 0)),
            clouds=today["clouds"]
        )
        return weather
    except Exception:
        logger.exception("Failed to fetch weather")
        return None
