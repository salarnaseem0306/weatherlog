from django.db.models import Count
from rest_framework.decorators import api_view
from rest_framework.response import Response

from readings.models import City

from .serializers import CitySerializer


@api_view(["GET"])
def city_list(request):
    cities = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    serializer = CitySerializer(cities, many=True)
    return Response(serializer.data)