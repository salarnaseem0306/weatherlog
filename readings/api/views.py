from django.db.models import Count
from rest_framework import generics

from readings.models import City

from .serializers import CitySerializer


class CityList(generics.ListAPIView):
    queryset = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    serializer_class = CitySerializer