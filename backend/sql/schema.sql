-- Schema for Wingz Ride Management API
-- MySQL 8.0, InnoDB, utf8mb4

CREATE TABLE IF NOT EXISTS users (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(50) NOT NULL,
    -- Added beyond spec §5 to support authentication (§2)
    password VARCHAR(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS rides (
    id_ride INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    id_rider INT NOT NULL,
    id_driver INT NOT NULL,
    pickup_latitude FLOAT NOT NULL,
    pickup_longitude FLOAT NOT NULL,
    dropoff_latitude FLOAT NOT NULL,
    dropoff_longitude FLOAT NOT NULL,
    pickup_time DATETIME NOT NULL,
    FOREIGN KEY (id_rider) REFERENCES users(id_user),
    FOREIGN KEY (id_driver) REFERENCES users(id_user),
    INDEX idx_ride_status (status),
    INDEX idx_ride_pickup_time (pickup_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ride_events (
    id_ride_event INT AUTO_INCREMENT PRIMARY KEY,
    id_ride INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (id_ride) REFERENCES rides(id_ride),
    INDEX idx_rideevent_created (created_at),
    INDEX idx_rideevent_ride_id (id_ride)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
