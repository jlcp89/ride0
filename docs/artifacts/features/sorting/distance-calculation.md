# Distance Calculation: Haversine Formula

## Formula
```
d = 6371 × 2 × arcsin(√(
    sin²((lat2 - lat1) / 2) +
    cos(lat1) × cos(lat2) × sin²((lng2 - lng1) / 2)
))
```
Result in kilometers.

## Implementation: RawSQL Annotation
```python
haversine = """
    6371 * 2 * ASIN(SQRT(
        POWER(SIN(RADIANS(pickup_latitude - %s) / 2), 2) +
        COS(RADIANS(%s)) * COS(RADIANS(pickup_latitude)) *
        POWER(SIN(RADIANS(pickup_longitude - %s) / 2), 2)
    ))
"""
qs = qs.annotate(distance=RawSQL(haversine, (lat, lat, lng)))
qs = qs.order_by('distance')
```

## Why RawSQL and not Django expressions?
Django doesn't have a built-in Haversine. Building one from Func/Sin/Cos is verbose
and less readable. RawSQL is pragmatic — it works on MySQL natively and on SQLite
with registered math functions.

## SQLite Compatibility for Tests
SQLite lacks RADIANS, SIN, COS, etc. We register them via a pytest autouse fixture:
```python
@pytest.fixture(autouse=True)
def _register_sqlite_math(db):
    from django.db import connection
    if connection.vendor == 'sqlite':
        import math
        connection.connection.create_function("RADIANS", 1, math.radians)
        # ... SIN, COS, ASIN, SQRT, POWER
```

## Test Verification Points
Use real coordinates with known distances:
- Zone 10, Guatemala City: 14.5995, -90.5131 (reference point)
- Zone 14: 14.5880, -90.4800 (~3.5 km from reference)
- Antigua: 14.5586, -90.7295 (~25 km from reference)
