from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from core.forms import CitySearchForm, SignUpForm
from core.models import WeatherSearch, FavoriteCity
from core.services import get_weather_by_city


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
                )
        else:
            if request.user.is_authenticated:
                WeatherSearch.objects.create(
                    user=request.user,
                    city=weather.city,
                    is_success=True,
                    error_message="",
                    temperature_c=int(round(weather.temp)),
                    description=weather.description or "",
                    wind_speed=float(weather.wind_speed) if weather.wind_speed is not None else None,
                    humidity=int(weather.humidity) if weather.humidity is not None else None,
                )

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
@require_POST
def toggle_favorite_city_view(request):
    city = (request.POST.get("city") or "").strip()
    next_url = request.POST.get("next") or reverse("weather_search")

    if not city:
        return redirect(next_url)

    obj = FavoriteCity.objects.filter(user=request.user, city__iexact=city).first()
    if obj:
        obj.delete()
    else:
        FavoriteCity.objects.create(user=request.user, city=city)

    return redirect(next_url)
