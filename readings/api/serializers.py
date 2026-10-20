from rest_framework import serializers

from readings.models import City, Reading


class CitySerializer(serializers.ModelSerializer):
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
    
    city_name = serializers.CharField(source="city.name", read_only=True)
    
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