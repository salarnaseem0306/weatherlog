# ORM queries

## 1. All readings for Lahore in July 2023
```python
Reading.objects.filter(city__name="Lahore", date__year=2023, date__month=7)
```
SQL: INNER JOIN readings_city, WHERE name = 'Lahore', year as BETWEEN range, month via django_date_extract, ORDER BY date (from Meta.ordering).

## 2. Hottest day of 2023 for each city
```python
for city in City.objects.all():
    city.readings.filter(date__year=2023).order_by("-max_temp").first()
```
SQL (per city): WHERE city_id = N AND date BETWEEN ..., ORDER BY max_temp DESC. One query per city (N+1).

## 3. Average max temperature per month for one city
```python
lahore.readings.aggregate(avg_max=Avg("max_temp"))
lahore.readings.annotate(month=TruncMonth("date")).values("month").annotate(avg_max=Avg("max_temp")).order_by("month")
```
SQL: SELECT django_date_trunc(month, date), AVG(max_temp) ... WHERE city_id = 1 GROUP BY 1 ORDER BY 1.

## 4. Cities with no readings
```python
City.objects.filter(readings__isnull=True)
```
SQL: LEFT OUTER JOIN readings_reading ... WHERE readings_reading.id IS NULL.