from django.contrib import admin
from django.urls import include, path

from core.views import (
    favorites_view,
    history_view,
    home_view,
    profile_view,
    report_detail_view,
    reports_view,
    signup_view,
    stats_view,
    toggle_favorite_city_view,
    weather_search_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("weather/", weather_search_view, name="weather_search"),
    path("favorites/", favorites_view, name="favorites"),
    path("history/", history_view, name="history"),
    path("favorites/toggle/", toggle_favorite_city_view, name="favorite_toggle"),
    path("profile/", profile_view, name="profile"),
    path("stats/", stats_view, name="stats"),
    path("reports/", reports_view, name="reports"),
    path("reports/<int:report_id>/", report_detail_view, name="report_detail"),
    path("accounts/signup/", signup_view, name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
]
