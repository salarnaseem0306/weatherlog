from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("cities", views.CityViewSet, basename="city")
router.register("readings", views.ReadingViewSet, basename="reading")

urlpatterns = [
    path("auth/token/", obtain_auth_token, name="api-token"),
    path("", include(router.urls)),
]