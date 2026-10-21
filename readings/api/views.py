from django.db.models import Avg, Count
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response

from readings.models import City, Reading

from .filters import ReadingFilter
from .permissions import IsOwnerOrStaffOrReadOnly
from .serializers import CitySerializer, CityStatsSerializer, ReadingSerializer


def _day(reading, field):
    """The date and one value of a reading, or None when there is no reading."""
    if reading is None:
        return None
    return {"date": reading.date, field: getattr(reading, field)}


def _round(value):
    return None if value is None else round(value, 1)


class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.annotate(reading_count=Count("readings")).order_by("name")
    serializer_class = CitySerializer
    permission_classes = [IsOwnerOrStaffOrReadOnly]

    @extend_schema(responses=ReadingSerializer(many=True))
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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "year", int, required=True, description="Calendar year, for example 2023"
            )
        ],
        responses={
            200: CityStatsSerializer,
            400: OpenApiResponse(description="year is missing or not a number"),
            404: OpenApiResponse(description="No such city, or no readings in that year"),
        },
    )
    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        """GET /api/cities/{id}/stats/?year=2023 : extremes and monthly averages."""
        city = self.get_object()

        year = request.query_params.get("year", "")
        if not year.isdigit():
            return Response(
                {"year": ["A year is required, for example ?year=2023."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        year = int(year)

        readings = city.readings.filter(date__year=year)

        # One GROUP BY query: the database averages each month
        monthly = list(
            readings.annotate(month=TruncMonth("date"))
            .values("month")
            .annotate(
                days=Count("id"),
                avg_max_temp=Avg("max_temp"),
                avg_min_temp=Avg("min_temp"),
                avg_humidity=Avg("humidity"),
            )
            .order_by("month")
        )
        if not monthly:
            return Response(
                {"detail": f"No readings for {city.name} in {year}."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Three ORDER BY ... LIMIT 1 queries; ties go to the earliest date
        hottest = (
            readings.filter(max_temp__isnull=False).order_by("-max_temp", "date").first()
        )
        coldest = (
            readings.filter(min_temp__isnull=False).order_by("min_temp", "date").first()
        )
        most_humid = (
            readings.filter(humidity__isnull=False).order_by("-humidity", "date").first()
        )

        return Response(
            {
                "city": city.name,
                "year": year,
                "hottest_day": _day(hottest, "max_temp"),
                "coldest_day": _day(coldest, "min_temp"),
                "most_humid_day": _day(most_humid, "humidity"),
                "monthly": [
                    {
                        "month": f"{row['month']:%Y-%m}",
                        "days": row["days"],
                        "avg_max_temp": _round(row["avg_max_temp"]),
                        "avg_min_temp": _round(row["avg_min_temp"]),
                        "avg_humidity": _round(row["avg_humidity"]),
                    }
                    for row in monthly
                ],
            }
        )


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