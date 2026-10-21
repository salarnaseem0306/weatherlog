from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter

from readings.models import City, Reading

from .filters import ReadingFilter
from .permissions import IsOwnerOrStaffOrReadOnly
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
        # same pagination as the other lists (a hand-written action must opt in)
        page = self.paginate_queryset(readings)
        serializer = ReadingSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ReadingViewSet(viewsets.ModelViewSet):
    queryset = Reading.objects.select_related("city", "created_by").order_by("-date")
    serializer_class = ReadingSerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]
    owner_field = "created_by"

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = ReadingFilter
    ordering_fields = ["date", "max_temp", "min_temp", "humidity"]  # allowed list
    ordering = ["-date"]  # default

    def perform_create(self, serializer):
        # created_by always comes from the logged-in user, never from the client
        serializer.save(created_by=self.request.user)