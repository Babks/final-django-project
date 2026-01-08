from dataclasses import dataclass
from typing import Optional, Iterable, Dict, Tuple, Any

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
    lat: float
    lon: float


def get_weather_by_city(city: str) -> Optional[WeatherResult]:
    api_key = getattr(settings, "OPENWEATHER_API_KEY", "") or ""
    api_key = api_key.strip()
    if not api_key:
        return None

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric", "lang": "ru"}

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
        coord = data.get("coord") or {}

        description = ""
        icon = ""
        if weather_list:
            description = str((weather_list[0] or {}).get("description") or "")
            icon = str((weather_list[0] or {}).get("icon") or "")

        icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png" if icon else ""

        lat = float(coord.get("lat"))
        lon = float(coord.get("lon"))

        return WeatherResult(
            city=name,
            country=country,
            temp=float(main.get("temp")),
            feels_like=float(main.get("feels_like")),
            description=description,
            humidity=int(main.get("humidity")),
            wind_speed=float(wind.get("speed") or 0),
            icon_url=icon_url,
            lat=lat,
            lon=lon,
        )
    except Exception:
        return None


_geo_cache: Dict[str, Tuple[float, float]] = {}


def geocode_city(city: str) -> Optional[Tuple[float, float]]:
    key = (city or "").strip().lower()
    if not key:
        return None

    if key in _geo_cache:
        return _geo_cache[key]

    api_key = getattr(settings, "OPENWEATHER_API_KEY", "") or ""
    api_key = api_key.strip()
    if not api_key:
        return None

    url = "https://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": api_key}

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

    if not isinstance(data, list) or not data:
        return None

    item = data[0] or {}
    try:
        lat = float(item.get("lat"))
        lon = float(item.get("lon"))
    except Exception:
        return None

    _geo_cache[key] = (lat, lon)
    return lat, lon


def calc_simple_fire_risk(temp_c: Optional[float], humidity: Optional[int], wind_speed: Optional[float]) -> int:
    t = float(temp_c) if temp_c is not None else 0.0
    h = int(humidity) if humidity is not None else 50
    w = float(wind_speed) if wind_speed is not None else 0.0

    # нормализация
    t_score = max(0.0, min(1.0, (t + 10.0) / 45.0))        # -10..35
    h_score = max(0.0, min(1.0, (100.0 - h) / 100.0))      # 0..100 (чем суше, тем больше)
    w_score = max(0.0, min(1.0, w / 20.0))                 # 0..20 м/с

    score = 100.0 * (0.45 * t_score + 0.35 * h_score + 0.20 * w_score)
    return int(round(max(0.0, min(100.0, score))))


def risk_color(score: int) -> str:
    if score < 25:
        return "green"
    if score < 50:
        return "yellow"
    if score < 75:
        return "orange"
    return "red"
