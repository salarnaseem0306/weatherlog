"""Tests for the JSON API under /api/ (DRF APIClient)."""
import secrets
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import City, Reading

PASSWORD = secrets.token_urlsafe(12)

def make_reading(city, day, **kwargs):
    defaults = {"max_temp": 30, "min_temp": 20, "humidity": 50}
    defaults.update(kwargs)
    return Reading.objects.create(city=city, date=day, **defaults)


def who(user):
    return user.username if user else "anonymous"


class ApiBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = City.objects.create(name="Lahore", country="Pakistan")
        cls.owner = User.objects.create_user("ali", password=PASSWORD)
        cls.other = User.objects.create_user("sara", password=PASSWORD)
        cls.staff = User.objects.create_user("boss", password=PASSWORD, is_staff=True)

    def login_as(self, user):
        """Send this user's token with every request; None means anonymous."""
        if user is None:
            self.client.credentials()
            return
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def new_day(self):
        self._days = getattr(self, "_days", 0) + 1
        return date(2030, 1, 1) + timedelta(days=self._days)

    def new_name(self):
        self._names = getattr(self, "_names", 0) + 1
        return f"City {self._names}"

    def reading_body(self, day=None, **overrides):
        body = {
            "city": self.city.pk,
            "date": str(day or self.new_day()),
            "max_temp": 30,
            "min_temp": 20,
            "humidity": 50,
        }
        body.update(overrides)
        return body


class PermissionTests(ApiBase):
    """One test per row of the Day 2 permissions table."""

    def test_get_is_open_to_everyone(self):
        reading = make_reading(self.city, date(2023, 1, 1), created_by=self.owner)
        urls = [
            reverse("city-list"),
            reverse("city-detail", args=[self.city.pk]),
            reverse("reading-list"),
            reverse("reading-detail", args=[reading.pk]),
        ]
        for user in (None, self.other, self.owner, self.staff):
            self.login_as(user)
            for url in urls:
                with self.subTest(user=who(user), url=url):
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_post_reading(self):
        cases = [(None, 401), (self.other, 201), (self.owner, 201), (self.staff, 201)]
        for user, expected in cases:
            self.login_as(user)
            with self.subTest(user=who(user)):
                response = self.client.post(
                    reverse("reading-list"), self.reading_body(), format="json"
                )
                self.assertEqual(response.status_code, expected)

    def test_change_reading(self):
        cases = [
            (None, {"put": 401, "patch": 401, "delete": 401}),
            (self.other, {"put": 403, "patch": 403, "delete": 403}),
            (self.owner, {"put": 200, "patch": 200, "delete": 204}),
            (self.staff, {"put": 200, "patch": 200, "delete": 204}),
        ]
        for user, codes in cases:
            for method, expected in codes.items():
                reading = make_reading(self.city, self.new_day(), created_by=self.owner)
                url = reverse("reading-detail", args=[reading.pk])
                self.login_as(user)
                with self.subTest(user=who(user), method=method):
                    if method == "put":
                        body = self.reading_body(day=reading.date, notes="changed")
                        response = self.client.put(url, body, format="json")
                    elif method == "patch":
                        response = self.client.patch(url, {"notes": "changed"}, format="json")
                    else:
                        response = self.client.delete(url)
                    self.assertEqual(response.status_code, expected)

    def test_change_city(self):
        staff_codes = {"post": 201, "put": 200, "patch": 200, "delete": 204}
        denied = {"post": 403, "put": 403, "patch": 403, "delete": 403}
        cases = [
            (None, {m: 401 for m in staff_codes}),
            (self.other, denied),
            (self.owner, denied),
            (self.staff, staff_codes),
        ]
        for user, codes in cases:
            for method, expected in codes.items():
                city = City.objects.create(name=self.new_name(), country="Pakistan")
                url = reverse("city-detail", args=[city.pk])
                self.login_as(user)
                with self.subTest(user=who(user), method=method):
                    if method == "post":
                        response = self.client.post(
                            reverse("city-list"),
                            {"name": self.new_name(), "country": "Pakistan"},
                            format="json",
                        )
                    elif method == "put":
                        response = self.client.put(
                            url,
                            {"name": self.new_name(), "country": "Pakistan"},
                            format="json",
                        )
                    elif method == "patch":
                        response = self.client.patch(url, {"country": "India"}, format="json")
                    else:
                        response = self.client.delete(url)
                    self.assertEqual(response.status_code, expected)


class ValidationTests(ApiBase):
    def setUp(self):
        self.login_as(self.owner)

    def post_reading(self, **overrides):
        return self.client.post(
            reverse("reading-list"), self.reading_body(**overrides), format="json"
        )

    def test_min_above_max_is_400_on_min_temp(self):
        response = self.post_reading(max_temp=20, min_temp=40)
        self.assertEqual(response.status_code, 400)
        self.assertIn("min_temp", response.json())
        self.assertEqual(Reading.objects.count(), 0)

    def test_duplicate_city_and_date_is_400_not_500(self):
        make_reading(self.city, date(2023, 1, 1))
        response = self.post_reading(date="2023-01-01")
        self.assertEqual(response.status_code, 400)
        self.assertIn("non_field_errors", response.json())
        self.assertEqual(Reading.objects.count(), 1)

    def test_humidity_outside_0_to_100_is_400_on_humidity(self):
        for value in (150, -1):
            with self.subTest(humidity=value):
                response = self.post_reading(humidity=value)
                self.assertEqual(response.status_code, 400)
                self.assertIn("humidity", response.json())

    def test_bad_date_is_400_on_date(self):
        response = self.post_reading(date="banana")
        self.assertEqual(response.status_code, 400)
        self.assertIn("date", response.json())

    def test_patch_that_breaks_min_max_is_400_and_changes_nothing(self):
        reading = make_reading(
            self.city, date(2023, 1, 1), created_by=self.owner, max_temp=30, min_temp=20
        )
        url = reverse("reading-detail", args=[reading.pk])
        response = self.client.patch(url, {"max_temp": 10}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("min_temp", response.json())
        reading.refresh_from_db()
        self.assertEqual(reading.max_temp, 30)


class CreatedByTests(ApiBase):
    def test_created_by_comes_from_the_token_not_the_client(self):
        self.login_as(self.owner)
        body = self.reading_body(created_by=self.other.username)
        response = self.client.post(reverse("reading-list"), body, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["created_by"], "ali")
        saved = Reading.objects.get(pk=response.json()["id"])
        self.assertEqual(saved.created_by, self.owner)

    def test_put_cannot_change_created_by(self):
        reading = make_reading(self.city, date(2023, 1, 1), created_by=self.owner)
        self.login_as(self.owner)
        body = self.reading_body(day=reading.date, created_by=self.other.username)
        url = reverse("reading-detail", args=[reading.pk])
        response = self.client.put(url, body, format="json")
        self.assertEqual(response.status_code, 200)
        reading.refresh_from_db()
        self.assertEqual(reading.created_by, self.owner)


class TokenTests(ApiBase):
    def test_valid_login_returns_the_users_token(self):
        response = self.client.post(
            reverse("api-token"),
            {"username": "ali", "password": PASSWORD},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["token"], Token.objects.get(user=self.owner).key)

    def test_wrong_password_is_400(self):
        response = self.client.post(
            reverse("api-token"),
            {"username": "ali", "password": "wrong"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("token", response.json())

    def test_wrong_token_is_401(self):
        reading = make_reading(self.city, date(2023, 1, 1), created_by=self.owner)
        self.client.credentials(HTTP_AUTHORIZATION="Token not-a-real-key")
        response = self.client.delete(reverse("reading-detail", args=[reading.pk]))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid token.")


class FilterOrderingStatsTests(ApiBase):
    """A small fixed data set, so every number can be checked by hand."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.karachi = City.objects.create(name="Karachi", country="Pakistan")
        rows = [
            # city, date, max, min, humidity, source
            (cls.city, date(2023, 1, 10), 20, 5, 40, "manual"),
            (cls.city, date(2023, 1, 20), 22, 7, 60, "manual"),
            (cls.city, date(2023, 2, 5), 25, 10, 70, "api"),
            (cls.city, date(2023, 7, 15), 40, 28, 30, "manual"),
            (cls.city, date(2023, 7, 16), 38, 30, 90, "manual"),
            (cls.city, date(2024, 1, 1), 50, 0, 100, "manual"),
            (cls.karachi, date(2023, 3, 3), 35, 25, 80, "manual"),
        ]
        for city, day, max_t, min_t, humidity, source in rows:
            make_reading(
                city, day, max_temp=max_t, min_temp=min_t, humidity=humidity, source=source
            )

    def list_readings(self, **params):
        return self.client.get(reverse("reading-list"), params)

    # --- filters ---

    def test_filter_by_city(self):
        response = self.list_readings(city=self.city.pk)
        self.assertEqual(response.json()["count"], 6)
        response = self.list_readings(city=self.karachi.pk)
        self.assertEqual(response.json()["count"], 1)

    def test_date_range_is_inclusive(self):
        # Lahore: 5 Feb and 15 Jul are both inside the range, both ends included
        response = self.list_readings(
            city=self.city.pk, date_after="2023-02-05", date_before="2023-07-15"
        )
        self.assertEqual(response.json()["count"], 2)
        # Without the city filter, Karachi's 3 March reading is inside the range too
        response = self.list_readings(date_after="2023-02-05", date_before="2023-07-15")
        self.assertEqual(response.json()["count"], 3)

    def test_filter_by_source(self):
        response = self.list_readings(source="api")
        self.assertEqual(response.json()["count"], 1)

    def test_bad_filter_values_are_400_not_an_empty_list(self):
        cases = [
            ("date_after", "banana"),
            ("date_before", "banana"),
            ("city", 999999),
            ("source", "banana"),
        ]
        for name, value in cases:
            with self.subTest(filter=name):
                response = self.list_readings(**{name: value})
                self.assertEqual(response.status_code, 400)
                self.assertIn(name, response.json())

    # --- ordering ---

    def test_ordering_uses_only_allowed_fields(self):
        first = lambda **p: self.list_readings(**p).json()["results"][0]
        self.assertEqual(first(ordering="date")["date"], "2023-01-10")
        self.assertEqual(first(ordering="-max_temp")["max_temp"], 50.0)
        # "notes" is not an allowed field, so it is ignored: default is newest first
        self.assertEqual(first(ordering="notes")["date"], "2024-01-01")

    # --- stats ---

    def stats_url(self, city=None):
        return reverse("city-stats", args=[(city or self.city).pk])

    def test_stats_numbers_for_2023(self):
        response = self.client.get(self.stats_url(), {"year": 2023})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "city": "Lahore",
                "year": 2023,
                "hottest_day": {"date": "2023-07-15", "max_temp": 40.0},
                "coldest_day": {"date": "2023-01-10", "min_temp": 5.0},
                "most_humid_day": {"date": "2023-07-16", "humidity": 90},
                "monthly": [
                    {"month": "2023-01", "days": 2, "avg_max_temp": 21.0,
                     "avg_min_temp": 6.0, "avg_humidity": 50.0},
                    {"month": "2023-02", "days": 1, "avg_max_temp": 25.0,
                     "avg_min_temp": 10.0, "avg_humidity": 70.0},
                    {"month": "2023-07", "days": 2, "avg_max_temp": 39.0,
                     "avg_min_temp": 29.0, "avg_humidity": 60.0},
                ],
            },
        )

    def test_stats_runs_a_fixed_number_of_queries(self):
        def queries():
            with CaptureQueriesContext(connection) as ctx:
                response = self.client.get(self.stats_url(), {"year": 2023})
            self.assertEqual(response.status_code, 200)
            return len(ctx)

        before = queries()
        for i in range(30):  # many more readings must not add queries
            make_reading(self.city, date(2023, 8, 1) + timedelta(days=i))
        after = queries()
        self.assertEqual(before, 5)
        self.assertEqual(after, before)

    def test_stats_errors(self):
        cases = [
            (self.stats_url(), {"year": 1999}, 404),
            (self.stats_url(), {}, 400),
            (self.stats_url(), {"year": "abc"}, 400),
            (reverse("city-stats", args=[999999]), {"year": 2023}, 404),
        ]
        for url, params, expected in cases:
            with self.subTest(params=params):
                self.assertEqual(self.client.get(url, params).status_code, expected)


class PaginationTests(ApiBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Reading.objects.bulk_create(
            [
                Reading(
                    city=cls.city,
                    date=date(2022, 1, 1) + timedelta(days=i),
                    max_temp=30,
                    min_temp=20,
                    humidity=50,
                )
                for i in range(105)
            ]
        )

    def page(self, **params):
        params.setdefault("city", self.city.pk)
        return self.client.get(reverse("reading-list"), params)

    def test_default_page_has_31_readings(self):
        data = self.page().json()
        self.assertEqual(data["count"], 105)
        self.assertEqual(len(data["results"]), 31)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

    def test_last_page_has_the_rest(self):
        data = self.page(page=4).json()
        self.assertEqual(len(data["results"]), 12)
        self.assertIsNone(data["next"])

    def test_page_size_is_capped_at_100(self):
        self.assertEqual(len(self.page(page_size=100).json()["results"]), 100)
        self.assertEqual(len(self.page(page_size=500).json()["results"]), 100)

    def test_invalid_page_is_404(self):
        self.assertEqual(self.page(page=999).status_code, 404)

    def test_city_readings_action_is_paginated(self):
        url = reverse("city-readings", args=[self.city.pk])
        data = self.client.get(url).json()
        self.assertEqual(data["count"], 105)
        self.assertEqual(len(data["results"]), 31)

    def test_city_list_has_the_pagination_shape(self):
        data = self.client.get(reverse("city-list")).json()
        self.assertEqual(set(data), {"count", "next", "previous", "results"})