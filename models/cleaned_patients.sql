-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: raw_patients
-- Generated Fixes:
--   * Fixed invalid age range in column 'age'
--   * Fixed invalid age range in column 'age'
--   * Fixed negative values in numeric column 'billing_amount'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Corrected inverted date logic between 'date_of_admission' and 'discharge_date'
--   * Corrected inverted date logic between 'admission_type' and 'discharge_date'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_raw_patients AS
SELECT 
    CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   CASE WHEN billing_amount < 0 THEN 0 ELSE billing_amount END AS billing_amount,
   COALESCE(name, 'UNKNOWN') AS name,
   CASE WHEN date_of_admission > discharge_date THEN discharge_date ELSE date_of_admission END AS date_of_admission,
   CASE WHEN date_of_admission > discharge_date THEN date_of_admission ELSE discharge_date END AS discharge_date,
   CASE WHEN admission_type > discharge_date THEN discharge_date ELSE admission_type END AS admission_type,
   CASE WHEN admission_type > discharge_date THEN admission_type ELSE discharge_date END AS discharge_date 
FROM raw_patients;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: staging_patients
-- Generated Fixes:
--   * Fixed invalid age range in column 'age'
--   * Fixed invalid age range in column 'age'
--   * Fixed negative values in numeric column 'billing_amount'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Corrected inverted date logic between 'date_of_admission' and 'discharge_date'
--   * Corrected inverted date logic between 'admission_type' and 'discharge_date'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_staging_patients AS
SELECT 
    CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   CASE WHEN billing_amount < 0 THEN 0 ELSE billing_amount END AS billing_amount,
   COALESCE(name, 'UNKNOWN') AS name,
   CASE WHEN date_of_admission > discharge_date THEN discharge_date ELSE date_of_admission END AS date_of_admission,
   CASE WHEN date_of_admission > discharge_date THEN date_of_admission ELSE discharge_date END AS discharge_date,
   CASE WHEN admission_type > discharge_date THEN discharge_date ELSE admission_type END AS admission_type,
   CASE WHEN admission_type > discharge_date THEN admission_type ELSE discharge_date END AS discharge_date 
FROM staging_patients;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_billing
-- Generated Fixes:
--   * Fixed negative values in numeric column 'billing_amount'
--   * Fixed negative values in numeric column 'length_of_stay_days'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Corrected inverted date logic between 'admission_type' and 'date_of_admission'
--   * Corrected inverted date logic between 'admission_type' and 'discharge_date'
--   * Corrected inverted date logic between 'date_of_admission' and 'discharge_date'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_mart_billing AS
SELECT 
    CASE WHEN billing_amount < 0 THEN 0 ELSE billing_amount END AS billing_amount,
   CASE WHEN length_of_stay_days < 0 THEN 0 ELSE length_of_stay_days END AS length_of_stay_days,
   COALESCE(name, 'UNKNOWN') AS name,
   CASE WHEN admission_type > date_of_admission THEN date_of_admission ELSE admission_type END AS admission_type,
   CASE WHEN admission_type > date_of_admission THEN admission_type ELSE date_of_admission END AS date_of_admission,
   CASE WHEN admission_type > discharge_date THEN discharge_date ELSE admission_type END AS admission_type,
   CASE WHEN admission_type > discharge_date THEN admission_type ELSE discharge_date END AS discharge_date,
   CASE WHEN date_of_admission > discharge_date THEN discharge_date ELSE date_of_admission END AS date_of_admission,
   CASE WHEN date_of_admission > discharge_date THEN date_of_admission ELSE discharge_date END AS discharge_date 
FROM mart_billing;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_demographics
-- Generated Fixes:
--   * Fixed invalid age range in column 'age'
--   * Fixed invalid age range in column 'age'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_mart_demographics AS
SELECT 
    CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   COALESCE(name, 'UNKNOWN') AS name 
FROM mart_demographics;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: customers
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_customers AS
SELECT 
    * 
FROM customers;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: inventory
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_inventory AS
SELECT 
    * 
FROM inventory;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: order_items
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_order_items AS
SELECT 
    * 
FROM order_items;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: orders
-- Generated Fixes:
--   * Replaced NULLs with 0 in column 'promo_id'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_orders AS
SELECT 
    COALESCE(promo_id, 0) AS promo_id 
FROM orders;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: products
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_products AS
SELECT 
    * 
FROM products;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: promotions
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_promotions AS
SELECT 
    * 
FROM promotions;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: returns
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_returns AS
SELECT 
    * 
FROM returns;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: shipments
-- Generated Fixes:
--   * Replaced NULLs with 0 in column 'delivered_date'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_shipments AS
SELECT 
    COALESCE(delivered_date, 0) AS delivered_date 
FROM shipments;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: suppliers
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_suppliers AS
SELECT 
    * 
FROM suppliers;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: warehouses
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_warehouses AS
SELECT 
    * 
FROM warehouses;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: raw_trips
-- Generated Fixes:
--   * Fixed negative values in numeric column 'pickup_longitude'
--   * Fixed negative values in numeric column 'dropoff_longitude'
--   * Fixed negative values in numeric column 'fare_amount'
--   * Fixed negative values in numeric column 'extra'
--   * Fixed negative values in numeric column 'mta_tax'
--   * Fixed negative values in numeric column 'tip_amount'
--   * Fixed negative values in numeric column 'tolls_amount'
--   * Fixed negative values in numeric column 'improvement_surcharge'
--   * Fixed negative values in numeric column 'total_amount'
--   * Corrected inverted date logic between 'tpep_pickup_datetime' and 'tpep_dropoff_datetime'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_raw_trips AS
SELECT 
    CASE WHEN pickup_longitude < 0 THEN 0 ELSE pickup_longitude END AS pickup_longitude,
   CASE WHEN dropoff_longitude < 0 THEN 0 ELSE dropoff_longitude END AS dropoff_longitude,
   CASE WHEN fare_amount < 0 THEN 0 ELSE fare_amount END AS fare_amount,
   CASE WHEN extra < 0 THEN 0 ELSE extra END AS extra,
   CASE WHEN mta_tax < 0 THEN 0 ELSE mta_tax END AS mta_tax,
   CASE WHEN tip_amount < 0 THEN 0 ELSE tip_amount END AS tip_amount,
   CASE WHEN tolls_amount < 0 THEN 0 ELSE tolls_amount END AS tolls_amount,
   CASE WHEN improvement_surcharge < 0 THEN 0 ELSE improvement_surcharge END AS improvement_surcharge,
   CASE WHEN total_amount < 0 THEN 0 ELSE total_amount END AS total_amount,
   CASE WHEN tpep_pickup_datetime > tpep_dropoff_datetime THEN tpep_dropoff_datetime ELSE tpep_pickup_datetime END AS tpep_pickup_datetime,
   CASE WHEN tpep_pickup_datetime > tpep_dropoff_datetime THEN tpep_pickup_datetime ELSE tpep_dropoff_datetime END AS tpep_dropoff_datetime 
FROM raw_trips;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: staging_trips
-- Generated Fixes:
--   * Fixed negative values in numeric column 'pickup_longitude'
--   * Fixed negative values in numeric column 'dropoff_longitude'
--   * Fixed negative values in numeric column 'trip_duration_min'
--   * Corrected inverted date logic between 'tpep_pickup_datetime' and 'tpep_dropoff_datetime'
--   * Corrected inverted date logic between 'tpep_pickup_datetime' and 'trip_date'
--   * Corrected inverted date logic between 'tpep_dropoff_datetime' and 'trip_date'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_staging_trips AS
SELECT 
    CASE WHEN pickup_longitude < 0 THEN 0 ELSE pickup_longitude END AS pickup_longitude,
   CASE WHEN dropoff_longitude < 0 THEN 0 ELSE dropoff_longitude END AS dropoff_longitude,
   CASE WHEN trip_duration_min < 0 THEN 0 ELSE trip_duration_min END AS trip_duration_min,
   CASE WHEN tpep_pickup_datetime > tpep_dropoff_datetime THEN tpep_dropoff_datetime ELSE tpep_pickup_datetime END AS tpep_pickup_datetime,
   CASE WHEN tpep_pickup_datetime > tpep_dropoff_datetime THEN tpep_pickup_datetime ELSE tpep_dropoff_datetime END AS tpep_dropoff_datetime,
   CASE WHEN tpep_pickup_datetime > trip_date THEN trip_date ELSE tpep_pickup_datetime END AS tpep_pickup_datetime,
   CASE WHEN tpep_pickup_datetime > trip_date THEN tpep_pickup_datetime ELSE trip_date END AS trip_date,
   CASE WHEN tpep_dropoff_datetime > trip_date THEN trip_date ELSE tpep_dropoff_datetime END AS tpep_dropoff_datetime,
   CASE WHEN tpep_dropoff_datetime > trip_date THEN tpep_dropoff_datetime ELSE trip_date END AS trip_date 
FROM staging_trips;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_daily_summary
-- Generated Fixes:
--   * 
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_mart_daily_summary AS
SELECT 
    * 
FROM mart_daily_summary;
