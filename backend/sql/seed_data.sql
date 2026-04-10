-- Seed Data for Wingz Ride Management API
-- Every row exists to test something specific.

-- ============================================================
-- USERS (7 total)
-- ============================================================
-- id=1: admin (password: adminpass123)
-- id=2-4: drivers (Chris H, Howard Y, Randy W) — match bonus SQL sample output
-- id=5-7: riders (Alice, Bob, Carol) — filter by rider_email tests

INSERT INTO users (id_user, role, first_name, last_name, email, phone_number, password) VALUES
(1, 'admin',  'Admin',  'User',  'admin@wingz.com',  '555-0001', 'pbkdf2_sha256$870000$26CDzVyj5UBvtRGjRIq943$ukWbXMBefm9/OIArA/1mtPsohxVhdhfDHFESAWYUedk='),
(2, 'driver', 'Chris',  'H',     'chris@wingz.com',  '555-0002', 'pbkdf2_sha256$870000$BgzVjAeEqnwmtaiYLh9bYV$cxUpFivf3ZLxxTrBT6YP7rgken1hB57WK2pBpbuJSgo='),
(3, 'driver', 'Howard', 'Y',     'howard@wingz.com', '555-0003', 'pbkdf2_sha256$870000$BgzVjAeEqnwmtaiYLh9bYV$cxUpFivf3ZLxxTrBT6YP7rgken1hB57WK2pBpbuJSgo='),
(4, 'driver', 'Randy',  'W',     'randy@wingz.com',  '555-0004', 'pbkdf2_sha256$870000$BgzVjAeEqnwmtaiYLh9bYV$cxUpFivf3ZLxxTrBT6YP7rgken1hB57WK2pBpbuJSgo='),
(5, 'rider',  'Alice',  'Rider', 'alice@wingz.com',  '555-0010', 'pbkdf2_sha256$870000$BgzVjAeEqnwmtaiYLh9bYV$cxUpFivf3ZLxxTrBT6YP7rgken1hB57WK2pBpbuJSgo='),
(6, 'rider',  'Bob',    'Rider', 'bob@wingz.com',    '555-0011', 'pbkdf2_sha256$870000$BgzVjAeEqnwmtaiYLh9bYV$cxUpFivf3ZLxxTrBT6YP7rgken1hB57WK2pBpbuJSgo='),
(7, 'rider',  'Carol',  'Rider', 'carol@wingz.com',  '555-0012', 'pbkdf2_sha256$870000$BgzVjAeEqnwmtaiYLh9bYV$cxUpFivf3ZLxxTrBT6YP7rgken1hB57WK2pBpbuJSgo=');

-- ============================================================
-- RIDES (24 total)
-- ============================================================
-- GPS zones for distance sorting tests:
--   Zone 10 (reference): 14.5995, -90.5131 (~0 km)
--   Zone 14:             14.5880, -90.4800 (~3.5 km)
--   Antigua:             14.5586, -90.7295 (~25 km)
--
-- Statuses: 8 en-route, 8 pickup, 8 dropoff
-- Drivers distributed across Chris(2), Howard(3), Randy(4)
-- Riders distributed across Alice(5), Bob(6), Carol(7)
-- pickup_time spread Jan-Apr 2024

-- January 2024 rides (6 rides)
INSERT INTO rides (id_ride, status, id_rider, id_driver, pickup_latitude, pickup_longitude, dropoff_latitude, dropoff_longitude, pickup_time) VALUES
(1,  'pickup',   5, 2, 14.5995, -90.5131, 14.6200, -90.5300, '2024-01-05 08:00:00'),
(2,  'pickup',   6, 3, 14.5880, -90.4800, 14.6100, -90.5000, '2024-01-10 09:00:00'),
(3,  'dropoff',  7, 4, 14.5586, -90.7295, 14.5700, -90.7100, '2024-01-15 10:00:00'),
(4,  'dropoff',  5, 2, 14.5995, -90.5131, 14.6300, -90.5200, '2024-01-20 11:00:00'),
(5,  'en-route', 6, 3, 14.5880, -90.4800, 14.6000, -90.5100, '2024-01-25 12:00:00'),
(6,  'en-route', 7, 4, 14.5586, -90.7295, 14.5800, -90.7000, '2024-01-30 13:00:00'),

-- February 2024 rides (6 rides)
(7,  'pickup',   5, 3, 14.5995, -90.5131, 14.6100, -90.5200, '2024-02-05 08:00:00'),
(8,  'pickup',   6, 4, 14.5880, -90.4800, 14.6000, -90.5000, '2024-02-10 09:00:00'),
(9,  'dropoff',  7, 2, 14.5586, -90.7295, 14.5700, -90.7100, '2024-02-15 10:00:00'),
(10, 'dropoff',  5, 3, 14.5995, -90.5131, 14.6200, -90.5300, '2024-02-20 11:00:00'),
(11, 'en-route', 6, 4, 14.5880, -90.4800, 14.6100, -90.5100, '2024-02-25 12:00:00'),
(12, 'en-route', 7, 2, 14.5586, -90.7295, 14.5900, -90.7000, '2024-02-28 13:00:00'),

-- March 2024 rides (6 rides)
(13, 'pickup',   5, 4, 14.5995, -90.5131, 14.6000, -90.5200, '2024-03-05 08:00:00'),
(14, 'pickup',   6, 2, 14.5880, -90.4800, 14.6100, -90.5000, '2024-03-10 09:00:00'),
(15, 'dropoff',  7, 3, 14.5586, -90.7295, 14.5800, -90.7100, '2024-03-15 10:00:00'),
(16, 'dropoff',  5, 4, 14.5995, -90.5131, 14.6300, -90.5300, '2024-03-20 11:00:00'),
(17, 'en-route', 6, 2, 14.5880, -90.4800, 14.6000, -90.5100, '2024-03-25 12:00:00'),
(18, 'en-route', 7, 3, 14.5586, -90.7295, 14.5700, -90.7000, '2024-03-30 13:00:00'),

-- April 2024 rides (6 rides) — includes recent rides for todays_ride_events
(19, 'pickup',   5, 2, 14.5995, -90.5131, 14.6100, -90.5200, '2024-04-05 08:00:00'),
(20, 'pickup',   6, 3, 14.5880, -90.4800, 14.6000, -90.5000, '2024-04-10 09:00:00'),
(21, 'dropoff',  7, 4, 14.5586, -90.7295, 14.5800, -90.7100, '2024-04-15 10:00:00'),
(22, 'dropoff',  5, 2, 14.5995, -90.5131, 14.6200, -90.5300, NOW()),
(23, 'en-route', 6, 3, 14.5880, -90.4800, 14.6100, -90.5100, NOW()),
(24, 'en-route', 7, 4, 14.5586, -90.7295, 14.5900, -90.7000, NOW());

-- ============================================================
-- RIDE EVENTS (68 total)
-- ============================================================
-- Pickup/dropoff pairs for bonus SQL (trips > 1hr)
-- Boundary cases: ride 5 = 59 min (excluded), ride 6 = 61 min (included)
-- Recent events for todays_ride_events testing on rides 22-24
-- Ride 1 has 20+ events to prove Prefetch filtering matters

-- ---- Ride 1: 20+ events (stress test for Prefetch filtering) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(1, 'Status changed to pickup',  '2024-01-05 08:00:00'),
(1, 'Status changed to dropoff', '2024-01-05 09:30:00'),
(1, 'Driver arrived at pickup',  '2024-01-05 08:05:00'),
(1, 'Rider confirmed pickup',    '2024-01-05 08:10:00'),
(1, 'En route to destination',   '2024-01-05 08:15:00'),
(1, 'Midway checkpoint',         '2024-01-05 08:30:00'),
(1, 'Traffic delay noted',       '2024-01-05 08:35:00'),
(1, 'Approaching destination',   '2024-01-05 08:50:00'),
(1, 'Arrived at destination',    '2024-01-05 09:00:00'),
(1, 'Rider confirmed dropoff',   '2024-01-05 09:05:00'),
(1, 'Payment processed',         '2024-01-05 09:10:00'),
(1, 'Rating submitted',          '2024-01-05 09:15:00'),
(1, 'Receipt sent',              '2024-01-05 09:20:00'),
(1, 'Trip summary generated',    '2024-01-05 09:22:00'),
(1, 'Driver feedback received',  '2024-01-05 09:25:00'),
(1, 'Route logged',              '2024-01-05 09:26:00'),
(1, 'Trip archived',             '2024-01-05 09:27:00'),
(1, 'Analytics event sent',      '2024-01-05 09:28:00'),
(1, 'Cleanup completed',         '2024-01-05 09:29:00'),
(1, 'Final status update',       '2024-01-05 09:30:00'),
(1, 'Post-trip notification',    '2024-01-05 09:31:00');

-- ---- Ride 2: > 1hr (75 min) — counted in bonus ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(2, 'Status changed to pickup',  '2024-01-10 09:00:00'),
(2, 'Status changed to dropoff', '2024-01-10 10:15:00');

-- ---- Ride 3: > 1hr (90 min) — counted in bonus ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(3, 'Status changed to pickup',  '2024-01-15 10:00:00'),
(3, 'Status changed to dropoff', '2024-01-15 11:30:00');

-- ---- Ride 4: > 1hr (80 min) — counted in bonus ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(4, 'Status changed to pickup',  '2024-01-20 11:00:00'),
(4, 'Status changed to dropoff', '2024-01-20 12:20:00');

-- ---- Ride 5: EXACTLY 59 min — boundary: excluded from bonus ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(5, 'Status changed to pickup',  '2024-01-25 12:00:00'),
(5, 'Status changed to dropoff', '2024-01-25 12:59:00');

-- ---- Ride 6: EXACTLY 61 min — boundary: included in bonus ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(6, 'Status changed to pickup',  '2024-01-30 13:00:00'),
(6, 'Status changed to dropoff', '2024-01-30 14:01:00');

-- ---- Ride 7: > 1hr (70 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(7, 'Status changed to pickup',  '2024-02-05 08:00:00'),
(7, 'Status changed to dropoff', '2024-02-05 09:10:00');

-- ---- Ride 8: > 1hr (85 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(8, 'Status changed to pickup',  '2024-02-10 09:00:00'),
(8, 'Status changed to dropoff', '2024-02-10 10:25:00');

-- ---- Ride 9: > 1hr (95 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(9, 'Status changed to pickup',  '2024-02-15 10:00:00'),
(9, 'Status changed to dropoff', '2024-02-15 11:35:00');

-- ---- Ride 10: < 1hr (45 min) — excluded ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(10, 'Status changed to pickup',  '2024-02-20 11:00:00'),
(10, 'Status changed to dropoff', '2024-02-20 11:45:00');

-- ---- Ride 11: < 1hr (30 min) — excluded ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(11, 'Status changed to pickup',  '2024-02-25 12:00:00'),
(11, 'Status changed to dropoff', '2024-02-25 12:30:00');

-- ---- Ride 12: > 1hr (100 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(12, 'Status changed to pickup',  '2024-02-28 13:00:00'),
(12, 'Status changed to dropoff', '2024-02-28 14:40:00');

-- ---- Ride 13: > 1hr (65 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(13, 'Status changed to pickup',  '2024-03-05 08:00:00'),
(13, 'Status changed to dropoff', '2024-03-05 09:05:00');

-- ---- Ride 14: < 1hr (50 min) — excluded ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(14, 'Status changed to pickup',  '2024-03-10 09:00:00'),
(14, 'Status changed to dropoff', '2024-03-10 09:50:00');

-- ---- Ride 15: > 1hr (75 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(15, 'Status changed to pickup',  '2024-03-15 10:00:00'),
(15, 'Status changed to dropoff', '2024-03-15 11:15:00');

-- ---- Ride 16: > 1hr (90 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(16, 'Status changed to pickup',  '2024-03-20 11:00:00'),
(16, 'Status changed to dropoff', '2024-03-20 12:30:00');

-- ---- Ride 17: < 1hr (40 min) — excluded ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(17, 'Status changed to pickup',  '2024-03-25 12:00:00'),
(17, 'Status changed to dropoff', '2024-03-25 12:40:00');

-- ---- Ride 18: > 1hr (80 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(18, 'Status changed to pickup',  '2024-03-30 13:00:00'),
(18, 'Status changed to dropoff', '2024-03-30 14:20:00');

-- ---- Ride 19: > 1hr (70 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(19, 'Status changed to pickup',  '2024-04-05 08:00:00'),
(19, 'Status changed to dropoff', '2024-04-05 09:10:00');

-- ---- Ride 20: < 1hr (55 min) — excluded ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(20, 'Status changed to pickup',  '2024-04-10 09:00:00'),
(20, 'Status changed to dropoff', '2024-04-10 09:55:00');

-- ---- Ride 21: > 1hr (120 min) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(21, 'Status changed to pickup',  '2024-04-15 10:00:00'),
(21, 'Status changed to dropoff', '2024-04-15 12:00:00');

-- ---- Rides 22-24: Recent events for todays_ride_events ----
-- Recent events (within last 24h) — should appear in API
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(22, 'Status changed to pickup',  NOW() - INTERVAL 2 HOUR),
(22, 'Status changed to dropoff', NOW() - INTERVAL 1 HOUR),
(23, 'Status changed to pickup',  NOW() - INTERVAL 3 HOUR),
(23, 'Status changed to dropoff', NOW() - INTERVAL 30 MINUTE),
(24, 'Status changed to pickup',  NOW() - INTERVAL 4 HOUR),
(24, 'Status changed to dropoff', NOW() - INTERVAL 15 MINUTE);

-- Old events (48h ago) — must NOT appear in todays_ride_events
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(22, 'Old status update',         NOW() - INTERVAL 48 HOUR),
(22, 'Old driver note',           NOW() - INTERVAL 48 HOUR),
(23, 'Old status update',         NOW() - INTERVAL 48 HOUR),
(23, 'Old driver note',           NOW() - INTERVAL 48 HOUR),
(24, 'Old status update',         NOW() - INTERVAL 48 HOUR);

-- ---- Multiple pickup events on ride 3 (tests MIN/MAX in bonus SQL) ----
INSERT INTO ride_events (id_ride, description, created_at) VALUES
(3, 'Status changed to pickup',  '2024-01-15 09:50:00'),
(3, 'Status changed to dropoff', '2024-01-15 11:45:00');
