from copy import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from readings.models import City, Reading


class CitySerializer(serializers.ModelSerializer):
    # Filled by .annotate(reading_count=Count("readings")) in the view's queryset,
    # so listing cities costs one query, not one query per city.
    reading_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "country",
            "latitude",
            "longitude",
            "created_at",
            "reading_count",
        ]
        read_only_fields = ["created_at"]


class ReadingSerializer(serializers.ModelSerializer):
    # city is written as an id, and also shown by name
    city_name = serializers.CharField(source="city.name", read_only=True)
    # shows the username (or null), never the user id or email
    created_by = serializers.SlugRelatedField(slug_field="username", read_only=True)

    class Meta:
        model = Reading
        fields = [
            "id",
            "city",
            "city_name",
            "date",
            "max_temp",
            "min_temp",
            "humidity",
            "notes",
            "source",
            "created_by",
        ]

    def validate(self, attrs):
        # Reuse the model's own rule (Reading.clean) so form, admin and API agree.
        # On PATCH, attrs holds only the changed fields, so start from the saved reading.
        candidate = copy(self.instance) if self.instance else Reading()
        for name, value in attrs.items():
            setattr(candidate, name, value)
        try:
            candidate.clean()
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict)
        return attrs


# The serializers below only describe the stats response for the API docs.
class HottestDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    max_temp = serializers.FloatField()


class ColdestDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    min_temp = serializers.FloatField()


class MostHumidDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    humidity = serializers.IntegerField()


class MonthlyStatsSerializer(serializers.Serializer):
    month = serializers.CharField(help_text="Month as YYYY-MM")
    days = serializers.IntegerField(help_text="Readings in that month")
    avg_max_temp = serializers.FloatField(allow_null=True)
    avg_min_temp = serializers.FloatField(allow_null=True)
    avg_humidity = serializers.FloatField(allow_null=True)


class CityStatsSerializer(serializers.Serializer):
    city = serializers.CharField()
    year = serializers.IntegerField()
    hottest_day = HottestDaySerializer(allow_null=True)
    coldest_day = ColdestDaySerializer(allow_null=True)
    most_humid_day = MostHumidDaySerializer(allow_null=True)
    monthly = MonthlyStatsSerializer(many=True)