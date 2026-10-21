"""Independent check of /api/cities/{id}/stats/ using plain Python loops."""
from collections import defaultdict

from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext, setup_test_environment

from readings.models import City

city = City.objects.get(pk=1)
year = 2023
rows = list(city.readings.filter(date__year=year))
print("readings in", year, ":", len(rows))

with_max = [r for r in rows if r.max_temp is not None]
with_min = [r for r in rows if r.min_temp is not None]
with_hum = [r for r in rows if r.humidity is not None]

# ties go to the earliest date, like the API
hottest = max(with_max, key=lambda r: (r.max_temp, -r.date.toordinal()))
coldest = min(with_min, key=lambda r: (r.min_temp, r.date.toordinal()))
humid = max(with_hum, key=lambda r: (r.humidity, -r.date.toordinal()))
print("hottest:", hottest.date, hottest.max_temp)
print("coldest:", coldest.date, coldest.min_temp)
print("most humid:", humid.date, humid.humidity)


def avg(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else None


months = defaultdict(list)
for r in rows:
    months[r.date.month].append(r)
for month in sorted(months):
    items = months[month]
    print(
        f"{year}-{month:02d}",
        len(items),
        avg(r.max_temp for r in items),
        avg(r.min_temp for r in items),
        avg(r.humidity for r in items),
    )

# Number of queries the endpoint really runs
setup_test_environment()
with CaptureQueriesContext(connection) as ctx:
    response = Client().get(f"/api/cities/1/stats/?year={year}")
print("status", response.status_code, "queries", len(ctx))