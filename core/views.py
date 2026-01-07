from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from core.forms import CitySearchForm
from core.models import WeatherSearch, FavoriteCity
from core.services import get_weather_by_city


def home_view(request):
    return render(request, "core/home.html")


def weather_search_view(request):
    form = CitySearchForm(request.POST or None)

    weather = None
    error_message = ""
    is_favorite = False

    if request.method == "POST" and form.is_valid():
        city = form.cleaned_data["city"].strip()
        weather = get_weather_by_city(city)

        if weather is None:
            error_message = "Не удалось получить данные. Проверьте название города или попробуйте позже."
            WeatherSearch.objects.create(
                user=request.user if request.user.is_authenticated else None,
                city=city,
                is_success=False,
                error_message=error_message,
                temperature_c=None,
                description="",
                wind_speed=None,
                humidity=None,
            )
        else:
            WeatherSearch.objects.create(
                user=request.user if request.user.is_authenticated else None,
                city=weather.city,
                is_success=True,
                error_message="",
                temperature_c=int(round(weather.temp)),
                description=weather.description or "",
                wind_speed=float(weather.wind_speed) if weather.wind_speed is not None else None,
                humidity=int(weather.humidity) if weather.humidity is not None else None,
            )

            if request.user.is_authenticated:
                is_favorite = FavoriteCity.objects.filter(user=request.user, city=weather.city).exists()

    context = {
        "form": form,
        "weather": weather,
        "error_message": error_message,
        "is_favorite": is_favorite,
    }
    return render(request, "core/weather_search.html", context)


@login_required
def history_view(request):
    items = WeatherSearch.objects.filter(user=request.user).order_by("-created_at")[:200]
    return render(request, "core/history.html", {"items": items})


@login_required
def favorites_view(request):
    items = FavoriteCity.objects.filter(user=request.user).order_by("city")
    return render(request, "core/favorites.html", {"items": items})


@login_required
@require_POST
def toggle_favorite_view(request):
    city = (request.POST.get("city") or "").strip()
    if not city:
        return redirect("weather_search")

    obj = FavoriteCity.objects.filter(user=request.user, city=city).first()
    if obj:
        obj.delete()
    else:
        FavoriteCity.objects.create(user=request.user, city=city)

    return redirect("weather_search")
