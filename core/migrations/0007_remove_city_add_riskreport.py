import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def copy_city_fk_to_text(apps, schema_editor):
    FavoriteCity = apps.get_model("core", "FavoriteCity")
    for row in FavoriteCity.objects.select_related("city").all():
        name = None
        try:
            if row.city_id:
                name = row.city.name
        except Exception:
            name = None
        if name:
            row.city_text = name
            row.save(update_fields=["city_text"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_alter_favoritecity_options_alter_favoritecity_user_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="favoritecity",
            name="city_text",
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
        migrations.RunPython(copy_city_fk_to_text, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="favoritecity",
            unique_together={("user", "city_text")},
        ),
        migrations.AlterModelOptions(
            name="favoritecity",
            options={"ordering": ["city_text"]},
        ),
        migrations.RemoveField(
            model_name="favoritecity",
            name="city",
        ),
        migrations.RenameField(
            model_name="favoritecity",
            old_name="city_text",
            new_name="city",
        ),
        migrations.AlterField(
            model_name="favoritecity",
            name="city",
            field=models.CharField(max_length=120),
        ),
        migrations.AlterField(
            model_name="favoritecity",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favorite_cities",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="favoritecity",
            unique_together={("user", "city")},
        ),
        migrations.AlterModelOptions(
            name="favoritecity",
            options={"ordering": ["city"]},
        ),
        migrations.DeleteModel(
            name="City",
        ),
        migrations.CreateModel(
            name="RiskReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day", models.DateField(db_index=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("avg_risk", models.IntegerField(blank=True, null=True)),
                ("max_risk", models.IntegerField(blank=True, null=True)),
                ("searches_count", models.IntegerField(default=0)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="risk_reports",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "searches",
                    models.ManyToManyField(
                        blank=True,
                        related_name="risk_reports",
                        to="core.weathersearch",
                    ),
                ),
            ],
            options={
                "ordering": ["-day", "-created_at"],
                "unique_together": {("user", "day")},
            },
        ),
    ]
