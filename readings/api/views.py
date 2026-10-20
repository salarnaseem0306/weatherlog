from django.db.models import Count
from rest_framework import viewsets

from readings.models import City

from .serializers import CitySerializer


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    serializer_class = CitySerializer