from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from .permissions import IsOwnerOrStaffOrReadOnly

from readings.models import City, Reading

from .serializers import CitySerializer, ReadingSerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    serializer_class = CitySerializer
    
    permission_classes = [IsOwnerOrStaffOrReadOnly]

    @action(detail=True, methods=["get"])
    def readings(self, request, pk=None):
        """GET /api/cities/{id}/readings/ : readings for one city, newest first."""
        city = self.get_object()
        readings = (
            city.readings.select_related("city", "created_by").order_by("-date")
        )
        serializer = ReadingSerializer(readings, many=True)
        return Response(serializer.data)


class ReadingViewSet(viewsets.ModelViewSet):
    queryset = Reading.objects.select_related("city", "created_by").order_by("-date")
    serializer_class = ReadingSerializer
   
    permission_classes = [IsOwnerOrStaffOrReadOnly]
    owner_field = "created_by"

    def perform_create(self, serializer):
        
        serializer.save(created_by=self.request.user)