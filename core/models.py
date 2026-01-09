from django.conf import settings
from django.db import models


class WeatherSearch(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="weather_searches",
    )
    city = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    is_success = models.BooleanField(default=False)
    error_message = models.CharField(max_length=255, blank=True)

    temperature_c = models.IntegerField(null=True, blank=True)
    description = models.CharField(max_length=120, blank=True)
    wind_speed = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(null=True, blank=True)

    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)
    risk_score = models.IntegerField(null=True, blank=True)

    firms_count = models.IntegerField(null=True, blank=True)
    firms_avg_confidence = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        status = "OK" if self.is_success else "ERR"
        return f"{self.city} ({status})"


class FavoriteCity(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="favorite_cities",
    )
    city = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "city")
        ordering = ["city"]

    def __str__(self) -> str:
        return f"{self.user} — {self.city}"


class RiskReport(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="risk_reports",
    )
    day = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    searches = models.ManyToManyField(
        WeatherSearch,
        related_name="risk_reports",
        blank=True,
    )

    avg_risk = models.IntegerField(null=True, blank=True)
    max_risk = models.IntegerField(null=True, blank=True)
    searches_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "day")
        ordering = ["-day", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user} — {self.day}"
