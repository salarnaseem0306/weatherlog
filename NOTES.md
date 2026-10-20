# NOTES

## schema.sql -> models.py
Django did: wrote CREATE TABLE from a Python class and added the `id` primary key for me.
Django hid: the SQL itself; I only see it by running `sqlmigrate`.

## migrate.py (PRAGMA user_version) -> makemigrations / migrate
Django did: generated the SQL, kept the steps in order, copied the data, and tracked the version in the `django_migrations` table.

Django hid: on SQLite, adding a field rebuilds the whole table, which can be slow on a big table.

## CHECK / UNIQUE in SQL -> constraints in Meta
Django did: turned `UniqueConstraint` and `CheckConstraint` into SQL `CONSTRAINT` clauses.
Django hid: `choices` and `on_delete` are enforced by Django in Python, not by the database.

## on_delete
I chose `on_delete=CASCADE` because the Day 2 delete page will show a confirmation that says how many readings will be deleted with the city, so no orphan readings are left behind.

## Admin username & password
admin 
Salar1122

## Admin constraint errors
Django checks UniqueConstraint and CheckConstraint in the admin form before saving, so I see a friendly message instead of a 500 error. The database constraints are still the last line of defence for data that skips the form.

## Project vs app
A project is the whole site (settings, root URLs). An app is one focused part of it, like `readings`, and one project can hold several apps.

## ORM vs my SqliteStore filter chain
The ORM builds the SQL for me and runs it only when I read the results (lazy evaluation). My SqliteStore filter chain loaded rows and filtered them in Python (or I wrote the SQL by hand); here Django does the filtering and joins in the database.

## N+1 queries
Finding the hottest day for each city with a loop runs one query per city. It works for 3 cities, but it would be slow for many.

## Post/Redirect/Get
Without a redirect, the browser remembers the POST, so pressing refresh asks to resend it and can create a duplicate. After a redirect, refresh only repeats the GET.

## CSRF
Without `{% csrf_token %}` Django returns 403 ("CSRF token missing"). The token proves the form came from our own page, so another site cannot make a logged-in browser submit changes for us.

## Why delete is POST only
A link that deletes on GET can be triggered by prefetching browsers, crawlers or an image tag, so changes must use POST (plus a CSRF token).


## Day 3: Query counts and N+1

Measured with `query_count.py` (CaptureQueriesContext), 5 cities in the database.

| Case | Before | After | Fix |
|------|--------|-------|-----|
| Reading count per city | 6 queries | 1 query | `annotate(Count("readings"))` |
| 31 readings with their city | 32 queries | 1 query | `select_related("city")` |
| Every city with its readings | 6 queries | 2 queries | `prefetch_related("readings")` |
| GET /cities/ | - | 1 query | annotate in `CityListView` |
| GET city detail, page 1 | - | 3 queries | paginator count + page query with `select_related("created_by")` |

**What N+1 is:** one query loads a list (the "1"), then the code touches a related
object on each row and Django runs one more query per row (the "N"). With 5 cities
that is 6 queries; with 500 cities it is 501.

**select_related vs prefetch_related:**
- `select_related` uses a SQL JOIN and fits ForeignKey / OneToOne (one related row per item).
- `prefetch_related` runs a second query and joins the result in Python. It fits reverse
  ForeignKey / many-to-many (many related rows per item), where a JOIN would repeat rows.

**Pagination:** the city detail page shows 31 readings per page (one month), and
`?year=2023&month=7` filters the readings. Invalid values are ignored. Only one page
of rows is loaded from the database at a time.


## Day 3: The three tests I would keep

If I could keep only three tests, I would keep:

1. `test_other_user_gets_403_on_update` (permissions). This is the one rule that
   protects other people's data. If it breaks, every user can edit every reading,
   and nothing on screen would warn me because the buttons are only hidden.
2. `test_duplicate_reading_shows_form_error_not_500` (views). I hit this bug while
   building the app: a duplicate date crashed with an IntegrityError and a 500 page.
   It is the "never an error page" rule from the exercise, tested through the real
   request, so it also proves that the form check and the view work together.
3. `test_duplicate_city_and_date_is_rejected` (model). The form check can be skipped
   (admin, shell, a future import command), so the database constraint is the real
   guarantee that a city has at most one reading per day.

The rest (page returns 200, 404 for a missing id, pagination) are useful but would be
noticed quickly by clicking around. These three protect things that fail silently.

## Exercise 5, Day 1: GET /api/cities/ three ways

Lines in `views.py` (non-blank): version 1 `@api_view` = 10, version 2 `ListAPIView` = 7,
version 3 `ReadOnlyModelViewSet` = 7. Each version is a separate commit.

Version 3 has the same line count as version 2 in `views.py`, but it serves two URLs
(list and detail) and the router adds an API root page, so the saving shows up as I add
endpoints, not on the first one.

What the viewset does that version 1 did by hand:
- Limits the allowed methods (version 1 needed `@api_view(["GET"])`; a read-only viewset
  only exposes list and retrieve).
- Builds the queryset and the serializer (`get_queryset()`, `get_serializer()`), so I
  do not write `many=True` or `Response(...)` myself.
- Looks up one object by id and returns a JSON 404 when it is missing (`get_object()`).
- Generates the URLs (`/cities/` and `/cities/{id}/`) through the router.
- Has hooks for pagination, filtering and permissions that I can switch on later without
  touching the view body.