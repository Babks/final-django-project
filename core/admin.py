from django.contrib import admin
from .models import Region, WeatherSnapshot, FireEvent, SavedQuery


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "lat", "lon", "created_at")
    search_fields = ("name", "country")


@admin.register(WeatherSnapshot)
class WeatherSnapshotAdmin(admin.ModelAdmin):
    list_display = ("region", "observed_at", "temperature_c", "humidity", "wind_speed")
    list_filter = ("region",)
    search_fields = ("region__name",)


@admin.register(FireEvent)
class FireEventAdmin(admin.ModelAdmin):
    list_display = ("region", "detected_at", "confidence", "source")
    list_filter = ("region", "source")
    search_fields = ("region__name",)


@admin.register(SavedQuery)
class SavedQueryAdmin(admin.ModelAdmin):
    list_display = ("user", "region", "query_type", "created_at")
    list_filter = ("query_type",)
    search_fields = ("user__username", "region__name")
