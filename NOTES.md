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