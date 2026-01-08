from django.contrib import admin
from django.urls import path, include

from core.views import (
    home_view,
    weather_search_view,
    favorites_view,
    history_view,
    toggle_favorite_city_view,
    signup_view,
    profile_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", home_view, name="home"),
    path("weather/", weather_search_view, name="weather_search"),

    path("favorites/", favorites_view, name="favorites"),
    path("history/", history_view, name="history"),
    path("favorites/toggle/", toggle_favorite_city_view, name="favorite_toggle"),

    path("profile/", profile_view, name="profile"),

    path("accounts/signup/", signup_view, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
]
