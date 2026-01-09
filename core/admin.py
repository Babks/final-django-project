from django.contrib import admin

from .models import FavoriteCity, RiskReport, WeatherSearch


@admin.register(WeatherSearch)
class WeatherSearchAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "city", "user", "is_success", "temperature_c", "risk_score")
    list_filter = ("is_success", "created_at")
    search_fields = ("city", "user__username", "user__email")
    readonly_fields = ("created_at",)


@admin.register(FavoriteCity)
class FavoriteCityAdmin(admin.ModelAdmin):
    list_display = ("id", "city", "user", "created_at")
    search_fields = ("city", "user__username", "user__email")
    readonly_fields = ("created_at",)


@admin.register(RiskReport)
class RiskReportAdmin(admin.ModelAdmin):
    list_display = ("id", "day", "user", "searches_count", "avg_risk", "max_risk", "created_at")
    list_filter = ("day",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)
