from dataclasses import dataclass
from typing import Optional, Dict, Tuple, Any, List, Iterable
import csv
import io
import math

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


def calc_simple_fire_risk(temp_c: Optional[float], humidity: Optional[int], wind_speed: Optional[float]) -> int:
    t = float(temp_c) if temp_c is not None else 0.0
    h = int(humidity) if humidity is not None else 50
    w = float(wind_speed) if wind_speed is not None else 0.0

    t_score = max(0.0, min(1.0, (t + 10.0) / 45.0))        # -10..35
    h_score = max(0.0, min(1.0, (100.0 - h) / 100.0))      # чем суше, тем больше
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


def _bbox_around_point(lat: float, lon: float, radius_km: float) -> Tuple[float, float, float, float]:
    delta_lat = radius_km / 111.0
    cos_lat = math.cos(math.radians(lat))
    if abs(cos_lat) < 1e-6:
        cos_lat = 1e-6
    delta_lon = radius_km / (111.0 * cos_lat)

    west = lon - delta_lon
    east = lon + delta_lon
    south = lat - delta_lat
    north = lat + delta_lat

    west = max(-180.0, min(180.0, west))
    east = max(-180.0, min(180.0, east))
    south = max(-90.0, min(90.0, south))
    north = max(-90.0, min(90.0, north))

    return west, south, east, north


def _looks_like_error_payload(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    return (
        t.startswith("<!doctype") or
        t.startswith("<html") or
        "error" in t[:200] or
        "invalid" in t[:200] or
        "not authorized" in t[:300] or
        "forbidden" in t[:300]
    )


def firms_get_area_events_for_source(
    *,
    lat: float,
    lon: float,
    source: str,
    radius_km: float = 50.0,
    day_range: int = 7,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    map_key = getattr(settings, "FIRMS_MAP_KEY", "") or ""
    map_key = map_key.strip()
    if not map_key:
        return None, "FIRMS_MAP_KEY не задан"

    source = (source or "").strip()
    if not source:
        return None, "FIRMS source пустой"

    day_range = int(day_range)
    if day_range < 1:
        day_range = 1
    if day_range > 30:
        day_range = 30

    west, south, east, north = _bbox_around_point(lat, lon, radius_km)
    area = f"{west:.6f},{south:.6f},{east:.6f},{north:.6f}"

    url = f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{map_key}/{source}/{area}/{day_range}"

    try:
        resp = requests.get(url, timeout=15)
    except Exception:
        return None, "Не удалось подключиться к FIRMS"

    if resp.status_code != 200:
        return None, f"FIRMS вернул HTTP {resp.status_code}"

    text = (resp.text or "").strip()
    if not text:
        return [], None

    if _looks_like_error_payload(text):
        return None, "FIRMS вернул ошибку (не CSV)"

    try:
        reader = csv.DictReader(io.StringIO(text))
        rows: List[Dict[str, Any]] = []
        for r in reader:
            if isinstance(r, dict):
                rows.append(r)
        return rows, None
    except Exception:
        return None, "Не удалось прочитать CSV от FIRMS"


def firms_get_area_events(
    lat: float,
    lon: float,
    radius_km: float = 50.0,
    day_range: int = 7,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], Optional[str]]:
    first = (getattr(settings, "FIRMS_SOURCE", "") or "").strip() or "VIIRS_SNPP_NRT"

    candidates = [
        first,
        "VIIRS_SNPP_NRT",
        "VIIRS_NOAA20_NRT",
        "MODIS_NRT",
    ]

    seen = set()
    ordered: List[str] = []
    for s in candidates:
        if s and s not in seen:
            seen.add(s)
            ordered.append(s)

    best_rows: Optional[List[Dict[str, Any]]] = None
    best_source: Optional[str] = None
    last_error: Optional[str] = None

    for src in ordered:
        rows, err = firms_get_area_events_for_source(
            lat=lat,
            lon=lon,
            source=src,
            radius_km=radius_km,
            day_range=day_range,
        )
        if rows is None:
            last_error = err or last_error
            continue

        if best_rows is None or len(rows) > len(best_rows):
            best_rows = rows
            best_source = src

        if best_rows and len(best_rows) >= 1:
            break

    if best_rows is None:
        return None, None, last_error or "FIRMS недоступен или вернул ошибку"

    return best_rows, best_source, None


def firms_aggregate(rows: Optional[List[Dict[str, Any]]]) -> Tuple[int, Optional[float]]:
    if rows is None:
        return 0, None
    if not rows:
        return 0, None  # пусто => не “0.0”, а “нет данных”

    conf_vals: List[float] = []
    for r in rows:
        raw = (
            r.get("confidence")
            or r.get("Confidence")
            or r.get("CONFIDENCE")
            or ""
        )
        try:
            conf_vals.append(float(str(raw).strip()))
        except Exception:
            pass

    avg_conf = (sum(conf_vals) / len(conf_vals)) if conf_vals else None
    return len(rows), avg_conf


def calc_fire_activity_score(firms_count: int, avg_confidence: Optional[float]) -> int:
    c = max(0, int(firms_count))

    count_score = math.log1p(min(c, 100)) / math.log1p(50)

    conf = None
    try:
        if avg_confidence is not None:
            conf = max(0.0, min(100.0, float(avg_confidence)))
    except Exception:
        conf = None

    conf_score = (conf / 100.0) if conf is not None else 0.5  # если нет confidence — среднее

    score = 100.0 * (0.65 * count_score + 0.35 * conf_score)
    return int(round(max(0.0, min(100.0, score))))


def calc_total_risk(weather_score: int, fire_score: int) -> int:
    score = 0.60 * float(weather_score) + 0.40 * float(fire_score)
    return int(round(max(0.0, min(100.0, score))))
