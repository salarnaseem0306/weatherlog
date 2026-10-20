from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("cities", views.CityViewSet, basename="city")

urlpatterns = [
    path("", include(router.urls)),
]