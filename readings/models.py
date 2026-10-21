from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class City(models.Model):
    name = models.CharField(max_length=100, unique=True)
    country = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "cities"

    def __str__(self):
        return self.name


class Reading(models.Model):
    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        API = "api", "API"

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,  # deleting a city also deletes its readings
        related_name="readings",
    )
    date = models.DateField()
    max_temp = models.FloatField(null=True, blank=True)
    min_temp = models.FloatField(null=True, blank=True)
    humidity = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    notes = models.TextField(blank=True)
    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        default=Source.MANUAL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_readings",
    )

    class Meta:
        ordering = ["date"]
        constraints = [
            models.UniqueConstraint(
                fields=["city", "date"],
                name="unique_reading_per_city_date",
            ),
            models.CheckConstraint(
                condition=models.Q(humidity__gte=0, humidity__lte=100),
                name="humidity_between_0_and_100",
            ),
        ]

    def __str__(self):
        return f"{self.city.name}, {self.date}"

    def clean(self):
        """Business rule shared by the HTML form, the admin and the API."""
        if (
            self.min_temp is not None
            and self.max_temp is not None
            and self.min_temp > self.max_temp
        ):
            raise ValidationError(
                {"min_temp": "Minimum temperature cannot be above the maximum."}
            )