-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: raw_trips
-- Generated Fixes:
--   * Fixed negative values in numeric column 'fare_amount'
--   * Fixed negative values in numeric column 'extra'
--   * Fixed negative values in numeric column 'mta_tax'
--   * Fixed negative values in numeric column 'tip_amount'
--   * Fixed negative values in numeric column 'tolls_amount'
--   * Fixed negative values in numeric column 'improvement_surcharge'
--   * Fixed negative values in numeric column 'total_amount'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_raw_trips AS
SELECT 
    VendorID AS VendorID,
   tpep_pickup_datetime AS tpep_pickup_datetime,
   tpep_dropoff_datetime AS tpep_dropoff_datetime,
   passenger_count AS passenger_count,
   trip_distance AS trip_distance,
   pickup_longitude AS pickup_longitude,
   pickup_latitude AS pickup_latitude,
   RateCodeID AS RateCodeID,
   store_and_fwd_flag AS store_and_fwd_flag,
   dropoff_longitude AS dropoff_longitude,
   dropoff_latitude AS dropoff_latitude,
   payment_type AS payment_type,
   CASE WHEN fare_amount < 0 THEN 0 ELSE fare_amount END AS fare_amount,
   CASE WHEN extra < 0 THEN 0 ELSE extra END AS extra,
   CASE WHEN mta_tax < 0 THEN 0 ELSE mta_tax END AS mta_tax,
   CASE WHEN tip_amount < 0 THEN 0 ELSE tip_amount END AS tip_amount,
   CASE WHEN tolls_amount < 0 THEN 0 ELSE tolls_amount END AS tolls_amount,
   CASE WHEN improvement_surcharge < 0 THEN 0 ELSE improvement_surcharge END AS improvement_surcharge,
   CASE WHEN total_amount < 0 THEN 0 ELSE total_amount END AS total_amount 
FROM raw_trips;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: staging_trips
-- Generated Fixes:
--   * Fixed negative values in numeric column 'trip_duration_min'
--   * Corrected inverted date logic between 'tpep_dropoff_datetime' and 'trip_date'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_staging_trips AS
SELECT 
    VendorID AS VendorID,
   tpep_pickup_datetime AS tpep_pickup_datetime,
   CASE WHEN tpep_dropoff_datetime > trip_date THEN trip_date ELSE tpep_dropoff_datetime END AS tpep_dropoff_datetime,
   passenger_count AS passenger_count,
   trip_distance AS trip_distance,
   pickup_longitude AS pickup_longitude,
   pickup_latitude AS pickup_latitude,
   RateCodeID AS RateCodeID,
   store_and_fwd_flag AS store_and_fwd_flag,
   dropoff_longitude AS dropoff_longitude,
   dropoff_latitude AS dropoff_latitude,
   payment_type AS payment_type,
   fare_amount AS fare_amount,
   extra AS extra,
   mta_tax AS mta_tax,
   tip_amount AS tip_amount,
   tolls_amount AS tolls_amount,
   improvement_surcharge AS improvement_surcharge,
   total_amount AS total_amount,
   trip_date AS trip_date,
   CASE WHEN trip_duration_min < 0 THEN 0 ELSE trip_duration_min END AS trip_duration_min,
   pipeline_status AS pipeline_status 
FROM staging_trips;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_daily_summary
-- Generated Fixes:
--   * No anomalies detected — table copied as-is.
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_mart_daily_summary AS
SELECT 
    trip_date AS trip_date,
   trip_count AS trip_count,
   total_fare AS total_fare,
   total_revenue AS total_revenue,
   avg_fare AS avg_fare,
   avg_distance AS avg_distance,
   avg_passengers AS avg_passengers,
   avg_duration_min AS avg_duration_min 
FROM mart_daily_summary;
