from django.contrib import admin
from django.urls import path

from core.views import home_view, weather_search_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home_view, name="home"),
    path("weather/", weather_search_view, name="weather_search"),
]
