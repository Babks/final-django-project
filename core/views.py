from django.shortcuts import render

from core.forms import CitySearchForm
from core.services import get_weather_by_city


def home_view(request):
    return render(request, "core/home.html")


def weather_search_view(request):
    form = CitySearchForm(request.POST or None)

    weather = None
    error_message = ""

    if request.method == "POST" and form.is_valid():
        city = form.cleaned_data["city"]
        weather = get_weather_by_city(city)
        if weather is None:
            error_message = "Не удалось получить данные. Проверьте название города или попробуйте позже."

    context = {
        "form": form,
        "weather": weather,
        "error_message": error_message,
    }
    return render(request, "core/weather_search.html", context)
