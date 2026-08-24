-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: raw_patients
-- Generated Fixes:
--   * Fixed invalid/negative age range in column 'age'
--   * Fixed negative values in numeric column 'billing_amount'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Corrected inverted date logic between 'date_of_admission' and 'discharge_date'
--   * Corrected inverted date logic between 'discharge_date' and 'date_of_admission'
--   * Flagged PII columns for governance review: name, medical_condition
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_raw_patients AS
SELECT 
    COALESCE(name, 'UNKNOWN') AS name,  -- [PII] Contains personally identifiable information
   CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   gender AS gender,
   blood_type AS blood_type,
   medical_condition AS medical_condition,  -- [PII] Contains personally identifiable information
   CASE WHEN date_of_admission > discharge_date THEN discharge_date ELSE date_of_admission END AS date_of_admission,
   doctor AS doctor,
   hospital AS hospital,
   insurance_provider AS insurance_provider,
   CASE WHEN billing_amount < 0 THEN 0 ELSE billing_amount END AS billing_amount,
   room_number AS room_number,
   admission_type AS admission_type,
   CASE WHEN discharge_date > date_of_admission THEN date_of_admission ELSE discharge_date END AS discharge_date,
   medication AS medication,
   test_results AS test_results 
FROM raw_patients;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: staging_patients
-- Generated Fixes:
--   * Fixed invalid/negative age range in column 'age'
--   * Fixed negative values in numeric column 'billing_amount'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Corrected inverted date logic between 'date_of_admission' and 'discharge_date'
--   * Corrected inverted date logic between 'discharge_date' and 'date_of_admission'
--   * Flagged PII columns for governance review: name, medical_condition
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_staging_patients AS
SELECT 
    COALESCE(name, 'UNKNOWN') AS name,  -- [PII] Contains personally identifiable information
   CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   gender AS gender,
   blood_type AS blood_type,
   medical_condition AS medical_condition,  -- [PII] Contains personally identifiable information
   CASE WHEN date_of_admission > discharge_date THEN discharge_date ELSE date_of_admission END AS date_of_admission,
   doctor AS doctor,
   hospital AS hospital,
   insurance_provider AS insurance_provider,
   CASE WHEN billing_amount < 0 THEN 0 ELSE billing_amount END AS billing_amount,
   room_number AS room_number,
   admission_type AS admission_type,
   CASE WHEN discharge_date > date_of_admission THEN date_of_admission ELSE discharge_date END AS discharge_date,
   medication AS medication,
   test_results AS test_results,
   gender_clean AS gender_clean,
   blood_type_clean AS blood_type_clean,
   condition_clean AS condition_clean,
   admission_type_clean AS admission_type_clean,
   test_results_clean AS test_results_clean,
   pipeline_status AS pipeline_status 
FROM staging_patients;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_billing
-- Generated Fixes:
--   * Fixed negative values in numeric column 'billing_amount'
--   * Fixed negative values in numeric column 'length_of_stay_days'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Corrected inverted date logic between 'date_of_admission' and 'discharge_date'
--   * Corrected inverted date logic between 'discharge_date' and 'date_of_admission'
--   * Flagged PII columns for governance review: name
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_mart_billing AS
SELECT 
    COALESCE(name, 'UNKNOWN') AS name,  -- [PII] Contains personally identifiable information
   hospital AS hospital,
   insurance_provider AS insurance_provider,
   admission_type AS admission_type,
   CASE WHEN billing_amount < 0 THEN 0 ELSE billing_amount END AS billing_amount,
   CASE WHEN date_of_admission > discharge_date THEN discharge_date ELSE date_of_admission END AS date_of_admission,
   CASE WHEN discharge_date > date_of_admission THEN date_of_admission ELSE discharge_date END AS discharge_date,
   CASE WHEN length_of_stay_days < 0 THEN 0 ELSE length_of_stay_days END AS length_of_stay_days,
   medication AS medication,
   pipeline_status AS pipeline_status 
FROM mart_billing;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_demographics
-- Generated Fixes:
--   * Fixed invalid/negative age range in column 'age'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Flagged PII columns for governance review: name, medical_condition
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_mart_demographics AS
SELECT 
    COALESCE(name, 'UNKNOWN') AS name,  -- [PII] Contains personally identifiable information
   CASE WHEN age < 0 OR age > 120 THEN NULL ELSE age END AS age,
   gender AS gender,
   blood_type AS blood_type,
   medical_condition AS medical_condition,  -- [PII] Contains personally identifiable information
   hospital AS hospital,
   test_results AS test_results,
   pipeline_status AS pipeline_status 
FROM mart_demographics;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: customers
-- Generated Fixes:
--   * Flagged PII columns for governance review: name, email, phone
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_customers AS
SELECT 
    customer_id AS customer_id,
   name AS name,  -- [PII] Contains personally identifiable information
   email AS email,  -- [PII] Contains personally identifiable information
   phone AS phone,  -- [PII] Contains personally identifiable information
   signup_date AS signup_date,
   country AS country,
   state AS state,
   city AS city,
   customer_segment AS customer_segment 
FROM customers;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: inventory
-- Generated Fixes:
--   * No anomalies detected — table copied as-is.
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_inventory AS
SELECT 
    inventory_id AS inventory_id,
   product_id AS product_id,
   warehouse_id AS warehouse_id,
   quantity_on_hand AS quantity_on_hand,
   reserved_quantity AS reserved_quantity,
   reorder_threshold AS reorder_threshold,
   last_restocked_date AS last_restocked_date 
FROM inventory;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: order_items
-- Generated Fixes:
--   * No anomalies detected — table copied as-is.
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_order_items AS
SELECT 
    order_item_id AS order_item_id,
   order_id AS order_id,
   product_id AS product_id,
   quantity AS quantity,
   unit_price AS unit_price,
   discount_pct AS discount_pct 
FROM order_items;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: orders
-- Generated Fixes:
--   * Replaced NULLs with 0 in column 'promo_id'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_orders AS
SELECT 
    order_id AS order_id,
   customer_id AS customer_id,
   order_date AS order_date,
   order_status AS order_status,
   total_amount AS total_amount,
   payment_method AS payment_method,
   shipping_country AS shipping_country,
   COALESCE(promo_id, 0) AS promo_id 
FROM orders;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: products
-- Generated Fixes:
--   * Flagged PII columns for governance review: name
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_products AS
SELECT 
    product_id AS product_id,
   name AS name,  -- [PII] Contains personally identifiable information
   category AS category,
   brand AS brand,
   price AS price,
   weight_kg AS weight_kg,
   supplier_id AS supplier_id 
FROM products;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: promotions
-- Generated Fixes:
--   * No anomalies detected — table copied as-is.
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_promotions AS
SELECT 
    promo_id AS promo_id,
   promo_code AS promo_code,
   description AS description,
   discount_pct AS discount_pct,
   valid_from AS valid_from,
   valid_until AS valid_until,
   applies_to_category AS applies_to_category,
   max_uses AS max_uses,
   status AS status 
FROM promotions;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: returns
-- Generated Fixes:
--   * No anomalies detected — table copied as-is.
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_returns AS
SELECT 
    return_id AS return_id,
   order_id AS order_id,
   product_id AS product_id,
   return_date AS return_date,
   refund_amount AS refund_amount,
   return_reason_code AS return_reason_code,
   processed_by AS processed_by 
FROM returns;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: shipments
-- Generated Fixes:
--   * Replaced NULLs with 0 in column 'delivered_date'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_shipments AS
SELECT 
    shipment_id AS shipment_id,
   order_id AS order_id,
   warehouse_id AS warehouse_id,
   carrier AS carrier,
   tracking_number AS tracking_number,
   shipped_date AS shipped_date,
   COALESCE(delivered_date, 0) AS delivered_date,
   shipment_state AS shipment_state 
FROM shipments;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: suppliers
-- Generated Fixes:
--   * Flagged PII columns for governance review: name
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_suppliers AS
SELECT 
    supplier_id AS supplier_id,
   name AS name,  -- [PII] Contains personally identifiable information
   country AS country,
   contract_start_date AS contract_start_date,
   status AS status 
FROM suppliers;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: warehouses
-- Generated Fixes:
--   * Flagged PII columns for governance review: name
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_warehouses AS
SELECT 
    warehouse_id AS warehouse_id,
   name AS name,  -- [PII] Contains personally identifiable information
   city AS city,
   state AS state,
   country AS country,
   capacity_units AS capacity_units,
   opened_date AS opened_date 
FROM warehouses;


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
--   * Corrected inverted date logic between 'tpep_pickup_datetime' and 'tpep_dropoff_datetime'
--   * Corrected inverted date logic between 'tpep_dropoff_datetime' and 'tpep_pickup_datetime'
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_raw_trips AS
SELECT 
    VendorID AS VendorID,
   CASE WHEN tpep_pickup_datetime > tpep_dropoff_datetime THEN tpep_dropoff_datetime ELSE tpep_pickup_datetime END AS tpep_pickup_datetime,
   CASE WHEN tpep_dropoff_datetime > tpep_pickup_datetime THEN tpep_pickup_datetime ELSE tpep_dropoff_datetime END AS tpep_dropoff_datetime,
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
-- =====================================================================

CREATE OR REPLACE TABLE cleaned_staging_trips AS
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
