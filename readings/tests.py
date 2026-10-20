from datetime import date, timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .forms import ReadingForm
from .models import City, Reading

PASSWORD = "pass12345"


def make_reading(city, day, **kwargs):
    """Create a reading with sensible defaults."""
    defaults = {"max_temp": 30, "min_temp": 20, "humidity": 50}
    defaults.update(kwargs)
    return Reading.objects.create(city=city, date=day, **defaults)


def form_data(**overrides):
    """Valid POST data for ReadingForm, with optional overrides."""
    data = {
        "date": "2023-07-01",
        "max_temp": "35",
        "min_temp": "25",
        "humidity": "50",
        "notes": "",
    }
    data.update(overrides)
    return data


class ModelTests(TestCase):
    def setUp(self):
        self.city = City.objects.create(name="Lahore", country="Pakistan")

    def test_str_methods(self):
        reading = make_reading(self.city, date(2023, 7, 1))
        self.assertEqual(str(self.city), "Lahore")
        self.assertEqual(str(reading), "Lahore, 2023-07-01")

    def test_duplicate_city_and_date_is_rejected(self):
        make_reading(self.city, date(2023, 7, 1))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_reading(self.city, date(2023, 7, 1))

    def test_humidity_outside_0_to_100_is_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_reading(self.city, date(2023, 7, 1), humidity=150)

    def test_deleting_city_deletes_its_readings(self):
        make_reading(self.city, date(2023, 7, 1))
        self.city.delete()
        self.assertEqual(Reading.objects.count(), 0)


class ReadingFormTests(TestCase):
    def setUp(self):
        self.city = City.objects.create(name="Lahore", country="Pakistan")

    def test_valid_data(self):
        form = ReadingForm(form_data(), city=self.city)
        self.assertTrue(form.is_valid())

    def test_min_temp_above_max_temp_is_invalid(self):
        form = ReadingForm(form_data(min_temp="40"), city=self.city)
        self.assertFalse(form.is_valid())
        self.assertIn("min_temp", form.errors)

    def test_humidity_above_100_is_invalid(self):
        form = ReadingForm(form_data(humidity="101"), city=self.city)
        self.assertFalse(form.is_valid())
        self.assertIn("humidity", form.errors)

    def test_duplicate_date_for_same_city_is_invalid(self):
        make_reading(self.city, date(2023, 7, 1))
        form = ReadingForm(form_data(), city=self.city)
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)

    def test_editing_a_reading_is_not_a_duplicate_of_itself(self):
        reading = make_reading(self.city, date(2023, 7, 1))
        form = ReadingForm(
            form_data(notes="edited"), instance=reading, city=self.city
        )
        self.assertTrue(form.is_valid())


class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = City.objects.create(name="Lahore", country="Pakistan")
        cls.owner = User.objects.create_user("ali", password=PASSWORD)
        cls.other = User.objects.create_user("sara", password=PASSWORD)
        cls.staff = User.objects.create_user(
            "boss", password=PASSWORD, is_staff=True
        )
        cls.reading = make_reading(
            cls.city, date(2023, 7, 1), created_by=cls.owner, notes="original"
        )

    def login(self, username):
        self.assertTrue(self.client.login(username=username, password=PASSWORD))



    def test_city_list_shows_cities(self):
        response = self.client.get(reverse("city_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lahore")

    def test_city_create_requires_login(self):
        url = reverse("city_create")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_anonymous_user_is_redirected_from_reading_update(self):
        url = reverse("reading_update", args=[self.reading.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")

    # --- pagination and filters ---

    def test_city_detail_is_paginated_31_per_page(self):
        for i in range(1, 40):  # 1 existing + 39 new = 40 readings
            make_reading(self.city, date(2023, 7, 1) + timedelta(days=i))
        url = reverse("city_detail", args=[self.city.pk])

        page1 = self.client.get(url)
        self.assertEqual(len(page1.context["readings"]), 31)

        page2 = self.client.get(url, {"page": 2})
        self.assertEqual(len(page2.context["readings"]), 9)

    def test_city_detail_filters_by_year_and_month(self):
        make_reading(self.city, date(2023, 8, 1))
        url = reverse("city_detail", args=[self.city.pk])
        response = self.client.get(url, {"year": 2023, "month": 8})
        self.assertEqual(len(response.context["readings"]), 1)

    def test_invalid_filter_values_are_ignored(self):
        url = reverse("city_detail", args=[self.city.pk])
        response = self.client.get(url, {"year": "abc", "month": "99"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["readings"]), 1)

    # --- creating readings ---

    def test_reading_create_sets_created_by(self):
        self.login("ali")
        url = reverse("reading_create", args=[self.city.pk])
        response = self.client.post(url, form_data(date="2023-08-01"))
        self.assertRedirects(
            response, reverse("city_detail", args=[self.city.pk])
        )
        reading = Reading.objects.get(date=date(2023, 8, 1))
        self.assertEqual(reading.created_by, self.owner)

    def test_duplicate_reading_shows_form_error_not_500(self):
        self.login("ali")
        url = reverse("reading_create", args=[self.city.pk])
        response = self.client.post(url, form_data(date="2023-07-01"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reading.objects.count(), 1)
        self.assertIn("date", response.context["form"].errors)

    # --- ownership permissions ---

    def test_owner_can_update_own_reading(self):
        self.login("ali")
        url = reverse("reading_update", args=[self.reading.pk])
        response = self.client.post(url, form_data(notes="edited"))
        self.assertRedirects(
            response, reverse("city_detail", args=[self.city.pk])
        )
        self.reading.refresh_from_db()
        self.assertEqual(self.reading.notes, "edited")

    def test_other_user_gets_403_on_update(self):
        self.login("sara")
        url = reverse("reading_update", args=[self.reading.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(
            self.client.post(url, form_data(notes="hacked")).status_code, 403
        )
        self.reading.refresh_from_db()
        self.assertEqual(self.reading.notes, "original")

    def test_other_user_cannot_delete(self):
        self.login("sara")
        url = reverse("reading_delete", args=[self.reading.pk])
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Reading.objects.filter(pk=self.reading.pk).exists())

    def test_staff_can_delete_any_reading(self):
        self.login("boss")
        url = reverse("reading_delete", args=[self.reading.pk])
        response = self.client.post(url)
        self.assertRedirects(
            response, reverse("city_detail", args=[self.city.pk])
        )
        self.assertFalse(Reading.objects.filter(pk=self.reading.pk).exists())

    def test_reading_without_owner_is_staff_only(self):
        old = make_reading(self.city, date(2023, 9, 1))  # created_by is None
        url = reverse("reading_update", args=[old.pk])

        self.login("sara")
        self.assertEqual(self.client.get(url).status_code, 403)

        self.login("boss")
        self.assertEqual(self.client.get(url).status_code, 200)

class PageAndAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = City.objects.create(name="Lahore", country="Pakistan")
        cls.owner = User.objects.create_user("ali", password=PASSWORD)
        cls.reading = make_reading(
            cls.city, date(2023, 7, 1), created_by=cls.owner
        )

    def protected_urls(self):
        """URLs that change data: anonymous users must not reach them."""
        return [
            reverse("city_create"),
            reverse("city_update", args=[self.city.pk]),
            reverse("city_delete", args=[self.city.pk]),
            reverse("reading_create", args=[self.city.pk]),
            reverse("reading_update", args=[self.reading.pk]),
            reverse("reading_delete", args=[self.reading.pk]),
        ]

    def test_every_page_returns_200_for_the_owner(self):
        self.client.login(username="ali", password=PASSWORD)
        urls = [
            reverse("city_list"),
            reverse("city_detail", args=[self.city.pk]),
        ] + self.protected_urls()
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_public_pages_work_for_anonymous_users(self):
        for url in [
            reverse("city_list"),
            reverse("city_detail", args=[self.city.pk]),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_missing_id_returns_404(self):
        self.client.login(username="ali", password=PASSWORD)
        urls = [
            reverse("city_detail", args=[9999]),
            reverse("city_update", args=[9999]),
            reverse("city_delete", args=[9999]),
            reverse("reading_create", args=[9999]),
            reverse("reading_update", args=[9999]),
            reverse("reading_delete", args=[9999]),
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 404)

    def test_anonymous_users_are_redirected_to_login(self):
        for url in self.protected_urls():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={url}",
                    fetch_redirect_response=False,
                )

    def test_anonymous_post_does_not_change_anything(self):
        self.client.post(reverse("city_delete", args=[self.city.pk]))
        self.client.post(reverse("reading_delete", args=[self.reading.pk]))
        self.assertTrue(City.objects.filter(pk=self.city.pk).exists())
        self.assertTrue(Reading.objects.filter(pk=self.reading.pk).exists())

    def test_delete_on_get_does_not_delete(self):
        self.client.login(username="ali", password=PASSWORD)
        self.client.get(reverse("reading_delete", args=[self.reading.pk]))
        self.client.get(reverse("city_delete", args=[self.city.pk]))
        self.assertTrue(Reading.objects.filter(pk=self.reading.pk).exists())
        self.assertTrue(City.objects.filter(pk=self.city.pk).exists())        