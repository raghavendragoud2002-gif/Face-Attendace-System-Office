-- schema.sql

-- Create Database
CREATE DATABASE IF NOT EXISTS face_attendance;
USE face_attendance;

-- 1. Admins Table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL, -- In a real app, use hashed passwords. For now, we might store plain or simple hash.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Employees Table (formerly persons)
CREATE TABLE IF NOT EXISTS employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    employee_id VARCHAR(50) UNIQUE NOT NULL, -- Custom ID like EMP001
    department VARCHAR(50),
    designation VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    image_path VARCHAR(255), -- Path to the stored face image
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    date DATE NOT NULL,
    first_in TIME, -- Replaces check_in_time
    last_seen TIME, -- Replaces check_out_time
    total_work_seconds INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'Absent', -- Present, Late, Absent
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (employee_id, date) -- One record per employee per day
);

-- Insert default admin (password: admin123)
-- You should change this immediately after deployment
INSERT IGNORE INTO admins (username, password_hash) VALUES ('admin', 'admin123');
