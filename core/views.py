from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Max
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.forms import CitySearchForm, SignUpForm
from core.models import WeatherSearch, FavoriteCity, RiskReport
from core.services import (
    get_weather_by_city,
    calc_simple_fire_risk,
    risk_color,
    firms_get_area_events,
    firms_aggregate,
    calc_fire_activity_score,
    calc_total_risk,
)


def home_view(request):
    return render(request, "core/home.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")

    return render(request, "registration/signup.html", {"form": form})


def _update_daily_report(user, weather_search_obj: WeatherSearch) -> None:
    if user is None or not getattr(user, "is_authenticated", False):
        return

    today = timezone.localdate()
    report, _ = RiskReport.objects.get_or_create(user=user, day=today)
    report.searches.add(weather_search_obj)

    agg = report.searches.filter(risk_score__isnull=False).aggregate(
        avg_val=Avg("risk_score"),
        max_val=Max("risk_score"),
        cnt=Count("id"),
    )

    report.searches_count = int(agg.get("cnt") or 0)

    avg_val = agg.get("avg_val")
    max_val = agg.get("max_val")

    report.avg_risk = int(round(float(avg_val))) if avg_val is not None else None
    report.max_risk = int(max_val) if max_val is not None else None
    report.save(update_fields=["searches_count", "avg_risk", "max_risk"])


def weather_search_view(request):
    form = CitySearchForm(request.POST or None)

    weather = None
    error_message = ""
    is_favorite = False

    if request.method == "POST" and form.is_valid():
        city = form.cleaned_data["city"]
        weather = get_weather_by_city(city)

        if weather is None:
            error_message = "Не удалось получить данные. Проверьте название города или попробуйте позже."
            if request.user.is_authenticated:
                WeatherSearch.objects.create(
                    user=request.user,
                    city=city,
                    is_success=False,
                    error_message=error_message,
                    temperature_c=None,
                    description="",
                    wind_speed=None,
                    humidity=None,
                    lat=None,
                    lon=None,
                    risk_score=None,
                    firms_count=None,
                    firms_avg_confidence=None,
                )
        else:
            if request.user.is_authenticated:
                weather_score = calc_simple_fire_risk(weather.temp, weather.humidity, weather.wind_speed)

                firms_rows, firms_source, firms_error = firms_get_area_events(
                    weather.lat,
                    weather.lon,
                    radius_km=50.0,
                    day_range=7,
                )
                firms_count, firms_avg_conf = firms_aggregate(firms_rows)

                fire_score = calc_fire_activity_score(firms_count, firms_avg_conf) if firms_rows is not None else 0
                total_risk = calc_total_risk(weather_score, fire_score)

                ws = WeatherSearch.objects.create(
                    user=request.user,
                    city=weather.city,
                    is_success=True,
                    error_message="",
                    temperature_c=int(round(weather.temp)),
                    description=weather.description or "",
                    wind_speed=float(weather.wind_speed) if weather.wind_speed is not None else None,
                    humidity=int(weather.humidity) if weather.humidity is not None else None,
                    lat=float(weather.lat),
                    lon=float(weather.lon),
                    risk_score=int(total_risk),
                    firms_count=int(firms_count) if firms_rows is not None else None,
                    firms_avg_confidence=float(firms_avg_conf) if (firms_rows is not None and firms_avg_conf is not None) else None,
                )

                _update_daily_report(request.user, ws)

                is_favorite = FavoriteCity.objects.filter(
                    user=request.user,
                    city__iexact=weather.city,
                ).exists()

    context = {
        "form": form,
        "weather": weather,
        "error_message": error_message,
        "is_favorite": is_favorite,
    }
    return render(request, "core/weather_search.html", context)


@login_required
def favorites_view(request):
    favorites = FavoriteCity.objects.filter(user=request.user).order_by("city")
    return render(request, "core/favorites.html", {"favorites": favorites})


@login_required
def history_view(request):
    history = WeatherSearch.objects.filter(user=request.user).order_by("-created_at")[:50]
    return render(request, "core/history.html", {"history": history})


@login_required
def profile_view(request):
    favorites_count = FavoriteCity.objects.filter(user=request.user).count()
    history_count = WeatherSearch.objects.filter(user=request.user).count()

    last_searches = WeatherSearch.objects.filter(user=request.user).order_by("-created_at")[:5]

    top_cities = (
        WeatherSearch.objects.filter(user=request.user, is_success=True)
        .values("city")
        .annotate(cnt=Count("id"))
        .order_by("-cnt", "city")[:5]
    )

    last_report = RiskReport.objects.filter(user=request.user).order_by("-day", "-created_at").first()

    context = {
        "favorites_count": favorites_count,
        "history_count": history_count,
        "last_searches": last_searches,
        "top_cities": top_cities,
        "last_report": last_report,
    }
    return render(request, "core/profile.html", context)


@login_required
def stats_view(request):
    total = WeatherSearch.objects.filter(user=request.user).count()
    ok = WeatherSearch.objects.filter(user=request.user, is_success=True).count()
    err = WeatherSearch.objects.filter(user=request.user, is_success=False).count()

    cities = list(
        WeatherSearch.objects.filter(
            user=request.user,
            is_success=True,
            temperature_c__isnull=False,
        )
        .values_list("city", flat=True)
        .order_by("city")
        .distinct()
    )

    selected_city = (request.GET.get("city") or "").strip()
    if not selected_city and cities:
        selected_city = cities[0]

    chart_labels = []
    chart_temps = []

    if selected_city:
        qs = (
            WeatherSearch.objects.filter(
                user=request.user,
                is_success=True,
                temperature_c__isnull=False,
                city__iexact=selected_city,
            )
            .order_by("-created_at")[:50]
        )
        rows = list(reversed(list(qs)))
        chart_labels = [r.created_at.strftime("%d.%m %H:%M") for r in rows]
        chart_temps = [r.temperature_c for r in rows]

    top_cities = (
        WeatherSearch.objects.filter(user=request.user, is_success=True)
        .values("city")
        .annotate(cnt=Count("id"), avg_temp=Avg("temperature_c"))
        .order_by("-cnt", "city")[:10]
    )

    recent = (
        WeatherSearch.objects.filter(user=request.user, is_success=True, lat__isnull=False, lon__isnull=False)
        .order_by("-created_at")[:200]
    )

    seen = set()
    markers = []

    for r in recent:
        key = (r.city or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)

        score = r.risk_score if r.risk_score is not None else calc_simple_fire_risk(r.temperature_c, r.humidity, r.wind_speed)
        color = risk_color(int(score))

        markers.append(
            {
                "city": r.city,
                "lat": float(r.lat),
                "lon": float(r.lon),
                "temp": r.temperature_c,
                "humidity": r.humidity,
                "wind": r.wind_speed,
                "score": int(score),
                "color": color,
                "firms_count": r.firms_count,
                "firms_avg_confidence": r.firms_avg_confidence,
                "time": r.created_at.strftime("%d.%m.%Y %H:%M"),
            }
        )

    context = {
        "total": total,
        "ok": ok,
        "err": err,
        "cities": cities,
        "selected_city": selected_city,
        "chart_labels": chart_labels,
        "chart_temps": chart_temps,
        "top_cities": top_cities,
        "markers": markers,
    }
    return render(request, "core/stats.html", context)

@login_required
def reports_view(request):
    reports = (
        RiskReport.objects.filter(user=request.user)
        .order_by("-day", "-created_at")[:60]
    )

    context = {
        "reports": reports,
    }
    return render(request, "core/reports.html", context)


@login_required
def report_detail_view(request, report_id: int):
    report = get_object_or_404(RiskReport, id=report_id, user=request.user)

    searches = (
        report.searches.all()
        .order_by("-created_at")[:200]
    )

    context = {
        "report": report,
        "searches": searches,
    }
    return render(request, "core/report_detail.html", context)


@login_required
@require_POST
def toggle_favorite_city_view(request):
    city_name = (request.POST.get("city") or "").strip()
    next_url = request.POST.get("next") or reverse("weather_search")

    if not city_name:
        return redirect(next_url)

    obj = FavoriteCity.objects.filter(user=request.user, city__iexact=city_name).first()
    if obj:
        obj.delete()
    else:
        FavoriteCity.objects.create(user=request.user, city=city_name)

    return redirect(next_url)
