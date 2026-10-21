from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from readings.models import City, Reading

from .serializers import CitySerializer, ReadingSerializer


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    serializer_class = CitySerializer
    # Temporary: replaced by IsOwnerOrStaffOrReadOnly in step 2.4
    permission_classes = [IsAuthenticatedOrReadOnly]

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
    # Temporary: replaced by IsOwnerOrStaffOrReadOnly in step 2.4
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        # created_by always comes from the logged-in user, never from the client
        serializer.save(created_by=self.request.user)