CREATE DATABASE IF NOT EXISTS web_traffic_management;
USE web_traffic_management;

CREATE TABLE IF NOT EXISTS servers (
    server_id INT PRIMARY KEY AUTO_INCREMENT,
    server_name VARCHAR(50) NOT NULL,
    port INT NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'UP'
);

CREATE TABLE IF NOT EXISTS resource_metrics (
    metric_id INT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    active_processes INT,
    active_requests INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(server_id)
);

CREATE TABLE IF NOT EXISTS traffic_logs (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    server_id INT NOT NULL,
    response_time FLOAT,
    routing_method VARCHAR(30),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (server_id) REFERENCES servers(server_id)
);

INSERT IGNORE INTO servers (server_id, server_name, port, status)
VALUES
(1, 'Server 1', 5001, 'UP'),
(2, 'Server 2', 5002, 'UP'),
(3, 'Server 3', 5003, 'UP');
