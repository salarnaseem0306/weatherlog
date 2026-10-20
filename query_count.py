"""Count database queries for N+1 vs optimized access (run via manage.py shell)."""
from django.db import connection
from django.db.models import Count
from django.test import Client
from django.test.utils import CaptureQueriesContext, setup_test_environment

from readings.models import City, Reading


def run(label, func):
    with CaptureQueriesContext(connection) as ctx:
        result = func()
    status = getattr(result, "status_code", "")
    print(f"{label}: {len(ctx)} queries {status}")


# 1. Reading count per city (city list page)
run("1a. city list count, N+1 (city.readings.count())",
    lambda: [c.readings.count() for c in City.objects.all()])
run("1b. city list count, annotate(Count)",
    lambda: [c.n for c in City.objects.annotate(n=Count("readings"))])

# 2. Reading.__str__ uses reading.city.name
run("2a. 31 readings, no select_related",
    lambda: [str(r) for r in Reading.objects.all()[:31]])
run("2b. 31 readings, select_related('city')",
    lambda: [str(r) for r in Reading.objects.select_related("city")[:31]])

# 3. All readings of every city
run("3a. every city's readings, N+1",
    lambda: [list(c.readings.all()) for c in City.objects.all()])
run("3b. every city's readings, prefetch_related",
    lambda: [list(c.readings.all()) for c in City.objects.prefetch_related("readings")])

# 4. Full pages through the test client
setup_test_environment()
client = Client()
first_city = City.objects.first()
run("4a. GET /cities/", lambda: client.get("/cities/"))
run("4b. GET city detail (page 1)", lambda: client.get(f"/cities/{first_city.pk}/"))