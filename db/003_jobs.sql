CREATE TABLE IF NOT EXISTS printanista.job_runs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  job_name VARCHAR(100) NOT NULL,
  source_type VARCHAR(50) NOT NULL,
  source_name TEXT NULL,
  status VARCHAR(30) NOT NULL,
  started_at DATETIME NOT NULL,
  finished_at DATETIME NULL,
  files_found INT DEFAULT 0,
  files_processed INT DEFAULT 0,
  files_skipped INT DEFAULT 0,
  rows_inserted INT DEFAULT 0,
  rows_updated INT DEFAULT 0,
  rows_ignored INT DEFAULT 0,
  details_json LONGTEXT NULL,
  error_text LONGTEXT NULL
);
CREATE TABLE IF NOT EXISTS printanista.job_run_items (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  job_run_id BIGINT NOT NULL,
  file_name TEXT NULL,
  file_sha1 CHAR(40) NULL,
  target_table VARCHAR(150) NULL,
  action_taken VARCHAR(50) NULL,
  rows_inserted INT DEFAULT 0,
  rows_updated INT DEFAULT 0,
  rows_ignored INT DEFAULT 0,
  message TEXT NULL
);
