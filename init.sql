CREATE TABLE IF NOT EXISTS printer_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    serial VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(150),
    client VARCHAR(150),
    ip_address VARCHAR(50),
    last_report VARCHAR(50),
    total_mono VARCHAR(50),
    total_color VARCHAR(50),
    raw_data TEXT,
    INDEX idx_serial (serial)
);