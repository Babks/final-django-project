from django.contrib import admin
from .models import WeatherSearch, FavoriteCity


@admin.register(WeatherSearch)
class WeatherSearchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "city",
        "user",
        "is_success",
        "temperature_c",
        "description",
    )
    list_filter = ("is_success", "created_at")
    search_fields = ("city", "user__username", "user__email")
    readonly_fields = ("created_at",)


@admin.register(FavoriteCity)
class FavoriteCityAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "user", "created_at")
    search_fields = ("city", "user__username", "user__email")
    readonly_fields = ("created_at",)
