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