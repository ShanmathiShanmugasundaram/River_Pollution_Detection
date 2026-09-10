CREATE DATABASE IF NOT EXISTS ganga_water_quality CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ganga_water_quality;

CREATE TABLE IF NOT EXISTS users (
  user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  mobile VARCHAR(30) NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_users_email (email)
);

CREATE TABLE IF NOT EXISTS stations (
  station_code VARCHAR(32) PRIMARY KEY,
  station_name VARCHAR(255) NOT NULL,
  state VARCHAR(80) NOT NULL,
  INDEX idx_stations_state (state)
);

CREATE TABLE IF NOT EXISTS historical_water_quality (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  station_code VARCHAR(32) NOT NULL,
  station_name VARCHAR(255) NOT NULL,
  state VARCHAR(80) NOT NULL,
  observation_year SMALLINT NOT NULL,
  observation_month_no TINYINT NOT NULL,
  round_no TINYINT NOT NULL,
  do_value DECIMAL(8,3) NOT NULL,
  ph_value DECIMAL(8,3) NOT NULL,
  bod_value DECIMAL(8,3) NOT NULL,
  UNIQUE KEY uq_historical_observation (station_code, observation_year, observation_month_no, round_no),
  INDEX idx_historical_station_month (station_code, observation_year, observation_month_no),
  FOREIGN KEY (station_code) REFERENCES stations(station_code)
);

CREATE TABLE IF NOT EXISTS forecast_2026 (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  station_code VARCHAR(32) NOT NULL,
  forecast_year SMALLINT NOT NULL,
  forecast_month_no TINYINT NOT NULL,
  forecast_month VARCHAR(20) NOT NULL,
  forecast_round TINYINT,
  pred_do DECIMAL(8,3), pred_ph DECIMAL(8,3), pred_bod DECIMAL(8,3),
  FOREIGN KEY (station_code) REFERENCES stations(station_code),
  UNIQUE KEY uq_forecast (station_code, forecast_month_no, forecast_round),
  INDEX idx_forecast_station_month (station_code, forecast_year, forecast_month_no)
);

CREATE TABLE IF NOT EXISTS wqi_predictions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  station_code VARCHAR(32) NOT NULL,
  forecast_month_no TINYINT NOT NULL,
  pred_wqi DECIMAL(8,3) NOT NULL,
  predicted_class VARCHAR(40) NOT NULL,
  FOREIGN KEY (station_code) REFERENCES stations(station_code),
  INDEX idx_wqi_station_month (station_code, forecast_month_no)
);

CREATE TABLE IF NOT EXISTS hotspot_analysis (
  station_code VARCHAR(32) PRIMARY KEY,
  forecast_months SMALLINT,
  mean_wqi DECIMAL(8,3), min_wqi DECIMAL(8,3), mean_do DECIMAL(8,3), min_do DECIMAL(8,3),
  mean_ph DECIMAL(8,3), min_ph DECIMAL(8,3), max_ph DECIMAL(8,3), mean_bod DECIMAL(8,3), max_bod DECIMAL(8,3),
  bod_exceed_months SMALLINT, do_violation_months SMALLINT, ph_violation_months SMALLINT, any_cpcb_violation_months SMALLINT,
  bod_exceed_percent DECIMAL(8,3), do_violation_percent DECIMAL(8,3), ph_violation_percent DECIMAL(8,3),
  cpcb_violation_percent DECIMAL(8,3), hotspot_level VARCHAR(40),
  FOREIGN KEY (station_code) REFERENCES stations(station_code),
  INDEX idx_hotspot_level (hotspot_level)
);

CREATE TABLE IF NOT EXISTS saprobic_assessment (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  location VARCHAR(255), state VARCHAR(80), year VARCHAR(20), season VARCHAR(30),
  saprobic_score DECIMAL(8,3), biological_quality VARCHAR(40), station_code VARCHAR(32),
  INDEX idx_bio_station (station_code), INDEX idx_bio_year_season (year, season)
);

CREATE TABLE IF NOT EXISTS biological_validation (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  station_code VARCHAR(32), location VARCHAR(255), state VARCHAR(80), year VARCHAR(20), season VARCHAR(30),
  saprobic_score DECIMAL(8,3), chemical_wqi DECIMAL(8,3), chemical_quality VARCHAR(40),
  mean_do DECIMAL(8,3), mean_ph DECIMAL(8,3), mean_bod DECIMAL(8,3),
  INDEX idx_validation_station (station_code)
);

CREATE TABLE IF NOT EXISTS live_uploads (
  upload_id CHAR(36) PRIMARY KEY,
  filename VARCHAR(255) NOT NULL,
  input_year SMALLINT NOT NULL,
  input_month_no TINYINT NOT NULL,
  input_month VARCHAR(20) NOT NULL,
  forecast_year SMALLINT NOT NULL,
  forecast_month_no TINYINT NOT NULL,
  forecast_month VARCHAR(20) NOT NULL,
  stations_processed INT NOT NULL DEFAULT 0,
  average_wqi DECIMAL(8,3),
  warnings INT NOT NULL DEFAULT 0,
  high_hotspots INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_live_input_month (input_year, input_month_no),
  INDEX idx_live_upload_created (created_at)
);

CREATE TABLE IF NOT EXISTS live_input_data (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  upload_id CHAR(36) NOT NULL,
  station_code VARCHAR(32) NOT NULL,
  station_name VARCHAR(255) NOT NULL,
  state VARCHAR(80) NOT NULL,
  input_year SMALLINT NOT NULL,
  input_month_no TINYINT NOT NULL,
  round_no TINYINT NOT NULL,
  do_value DECIMAL(8,3) NOT NULL,
  ph_value DECIMAL(8,3) NOT NULL,
  bod_value DECIMAL(8,3) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (upload_id) REFERENCES live_uploads(upload_id) ON DELETE CASCADE,
  UNIQUE KEY uq_live_input_record (upload_id, station_code, round_no),
  INDEX idx_live_input_station_month (station_code, input_year, input_month_no)
);

CREATE TABLE IF NOT EXISTS live_predictions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  upload_id CHAR(36) NOT NULL,
  station_code VARCHAR(32) NOT NULL,
  station_name VARCHAR(255) NOT NULL,
  state VARCHAR(80) NOT NULL,
  forecast_year SMALLINT NOT NULL,
  forecast_month_no TINYINT NOT NULL,
  predicted_do DECIMAL(8,3) NOT NULL,
  predicted_ph DECIMAL(8,3) NOT NULL,
  predicted_bod DECIMAL(8,3) NOT NULL,
  predicted_wqi DECIMAL(8,3) NOT NULL,
  wqi_class VARCHAR(40) NOT NULL,
  hotspot_level VARCHAR(40) NOT NULL,
  cpcb_do_status VARCHAR(20) NOT NULL,
  cpcb_ph_status VARCHAR(20) NOT NULL,
  cpcb_bod_status VARCHAR(20) NOT NULL,
  cpcb_violation_percent DECIMAL(8,3) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (upload_id) REFERENCES live_uploads(upload_id) ON DELETE CASCADE,
  UNIQUE KEY uq_live_prediction (upload_id, station_code),
  INDEX idx_live_prediction_station_month (station_code, forecast_year, forecast_month_no),
  INDEX idx_live_prediction_hotspot (hotspot_level)
);

CREATE TABLE IF NOT EXISTS notifications (
  notification_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  upload_id CHAR(36) NOT NULL,
  station_code VARCHAR(32) NOT NULL,
  station_name VARCHAR(255) NOT NULL,
  state VARCHAR(80) NOT NULL,
  severity VARCHAR(30) NOT NULL,
  input_month VARCHAR(30) NOT NULL,
  forecast_month VARCHAR(30) NOT NULL,
  predicted_wqi DECIMAL(8,3) NOT NULL,
  predicted_do DECIMAL(8,3) NOT NULL,
  predicted_ph DECIMAL(8,3) NOT NULL,
  predicted_bod DECIMAL(8,3) NOT NULL,
  hotspot_level VARCHAR(40) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (upload_id) REFERENCES live_uploads(upload_id) ON DELETE CASCADE,
  UNIQUE KEY uq_high_hotspot_notification (upload_id, station_code, severity),
  INDEX idx_notifications_read_created (is_read, created_at),
  INDEX idx_notifications_severity (severity)
);
