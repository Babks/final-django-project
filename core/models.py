from django.conf import settings
from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=120, unique=True)
    country = models.CharField(max_length=120, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WeatherSnapshot(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="weather_snapshots")
    observed_at = models.DateTimeField()
    temperature_c = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-observed_at"]

    def __str__(self):
        return f"{self.region} @ {self.observed_at:%Y-%m-%d %H:%M}"


class FireEvent(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="fire_events")
    detected_at = models.DateTimeField()
    lat = models.FloatField()
    lon = models.FloatField()
    confidence = models.IntegerField(null=True, blank=True)
    source = models.CharField(max_length=60, default="FIRMS")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.region} fire @ {self.detected_at:%Y-%m-%d}"


class SavedQuery(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_queries")
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="saved_queries")
    query_type = models.CharField(max_length=20, choices=[("favorite", "favorite"), ("history", "history")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.region} ({self.query_type})"
