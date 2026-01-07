from django.contrib import admin
from django.urls import path

from core.views import (
    home_view,
    weather_search_view,
    history_view,
    favorites_view,
    toggle_favorite_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("weather/", weather_search_view, name="weather_search"),
    path("history/", history_view, name="history"),
    path("favorites/", favorites_view, name="favorites"),
    path("favorites/toggle/", toggle_favorite_view, name="toggle_favorite"),
]
