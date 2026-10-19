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