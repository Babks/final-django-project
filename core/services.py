from dataclasses import dataclass
from typing import Optional

import requests
from django.conf import settings


@dataclass(frozen=True)
class WeatherResult:
    city: str
    country: str
    temp: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    icon_url: str


def get_weather_by_city(city: str) -> Optional[WeatherResult]:
    api_key = getattr(settings, "OPENWEATHER_API_KEY", "") or ""
    api_key = api_key.strip()
    if not api_key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "ru",
    }

    try:
        resp = requests.get(url, params=params, timeout=8)
    except Exception:
        return None

    if resp.status_code != 200:
        return None

    try:
        data = resp.json()
    except Exception:
        return None

    try:
        name = str(data.get("name") or city)
        sys_data = data.get("sys") or {}
        country = str(sys_data.get("country") or "")
        main = data.get("main") or {}
        weather_list = data.get("weather") or []
        wind = data.get("wind") or {}

        description = ""
        icon = ""
        if weather_list:
            description = str((weather_list[0] or {}).get("description") or "")
            icon = str((weather_list[0] or {}).get("icon") or "")

        icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png" if icon else ""

        return WeatherResult(
            city=name,
            country=country,
            temp=float(main.get("temp")),
            feels_like=float(main.get("feels_like")),
            description=description,
            humidity=int(main.get("humidity")),
            wind_speed=float(wind.get("speed") or 0),
            icon_url=icon_url,
        )
    except Exception:
        return None
