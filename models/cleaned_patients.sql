-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: raw_patients
-- Generated Fixes:
--   * Flagged PII columns for governance review: name, medical_condition, medication
-- =====================================================================

DROP TABLE IF EXISTS cleaned_raw_patients;

CREATE TABLE cleaned_raw_patients AS
SELECT 
    name AS name,  -- [PII] Contains personally identifiable information
   age AS age,
   gender AS gender,
   blood_type AS blood_type,
   medical_condition AS medical_condition,  -- [PII] Contains personally identifiable information
   date_of_admission AS date_of_admission,
   doctor AS doctor,
   hospital AS hospital,
   insurance_provider AS insurance_provider,
   billing_amount AS billing_amount,
   room_number AS room_number,
   admission_type AS admission_type,
   discharge_date AS discharge_date,
   medication AS medication,  -- [PII] Contains personally identifiable information
   test_results AS test_results 
FROM raw_patients;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: staging_patients
-- Generated Fixes:
--   * Flagged PII columns for governance review: name, medical_condition, medication
-- =====================================================================

DROP TABLE IF EXISTS cleaned_staging_patients;

CREATE TABLE cleaned_staging_patients AS
SELECT 
    name AS name,  -- [PII] Contains personally identifiable information
   age AS age,
   gender AS gender,
   blood_type AS blood_type,
   medical_condition AS medical_condition,  -- [PII] Contains personally identifiable information
   date_of_admission AS date_of_admission,
   doctor AS doctor,
   hospital AS hospital,
   insurance_provider AS insurance_provider,
   billing_amount AS billing_amount,
   room_number AS room_number,
   admission_type AS admission_type,
   discharge_date AS discharge_date,
   medication AS medication,  -- [PII] Contains personally identifiable information
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
--   * Flagged PII columns for governance review: name, medication
-- =====================================================================

DROP TABLE IF EXISTS cleaned_mart_billing;

CREATE TABLE cleaned_mart_billing AS
SELECT 
    name AS name,  -- [PII] Contains personally identifiable information
   hospital AS hospital,
   insurance_provider AS insurance_provider,
   admission_type AS admission_type,
   billing_amount AS billing_amount,
   date_of_admission AS date_of_admission,
   discharge_date AS discharge_date,
   length_of_stay_days AS length_of_stay_days,
   medication AS medication,  -- [PII] Contains personally identifiable information
   pipeline_status AS pipeline_status 
FROM mart_billing;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_demographics
-- Generated Fixes:
--   * Flagged PII columns for governance review: name, medical_condition
-- =====================================================================

DROP TABLE IF EXISTS cleaned_mart_demographics;

CREATE TABLE cleaned_mart_demographics AS
SELECT 
    name AS name,  -- [PII] Contains personally identifiable information
   age AS age,
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

DROP TABLE IF EXISTS cleaned_customers;

CREATE TABLE cleaned_customers AS
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

DROP TABLE IF EXISTS cleaned_inventory;

CREATE TABLE cleaned_inventory AS
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

DROP TABLE IF EXISTS cleaned_order_items;

CREATE TABLE cleaned_order_items AS
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
--   * No anomalies detected — table copied as-is.
-- =====================================================================

DROP TABLE IF EXISTS cleaned_orders;

CREATE TABLE cleaned_orders AS
SELECT 
    order_id AS order_id,
   customer_id AS customer_id,
   order_date AS order_date,
   order_status AS order_status,
   total_amount AS total_amount,
   payment_method AS payment_method,
   shipping_country AS shipping_country,
   promo_id AS promo_id 
FROM orders;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: products
-- Generated Fixes:
--   * Flagged PII columns for governance review: name
-- =====================================================================

DROP TABLE IF EXISTS cleaned_products;

CREATE TABLE cleaned_products AS
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

DROP TABLE IF EXISTS cleaned_promotions;

CREATE TABLE cleaned_promotions AS
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

DROP TABLE IF EXISTS cleaned_returns;

CREATE TABLE cleaned_returns AS
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
--   * No anomalies detected — table copied as-is.
-- =====================================================================

DROP TABLE IF EXISTS cleaned_shipments;

CREATE TABLE cleaned_shipments AS
SELECT 
    shipment_id AS shipment_id,
   order_id AS order_id,
   warehouse_id AS warehouse_id,
   carrier AS carrier,
   tracking_number AS tracking_number,
   shipped_date AS shipped_date,
   delivered_date AS delivered_date,
   shipment_state AS shipment_state 
FROM shipments;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: suppliers
-- Generated Fixes:
--   * Flagged PII columns for governance review: name
-- =====================================================================

DROP TABLE IF EXISTS cleaned_suppliers;

CREATE TABLE cleaned_suppliers AS
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

DROP TABLE IF EXISTS cleaned_warehouses;

CREATE TABLE cleaned_warehouses AS
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
--   * No anomalies detected — table copied as-is.
-- =====================================================================

DROP TABLE IF EXISTS cleaned_raw_trips;

CREATE TABLE cleaned_raw_trips AS
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
   total_amount AS total_amount 
FROM raw_trips;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: staging_trips
-- Generated Fixes:
--   * No anomalies detected — table copied as-is.
-- =====================================================================

DROP TABLE IF EXISTS cleaned_staging_trips;

CREATE TABLE cleaned_staging_trips AS
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
   trip_duration_min AS trip_duration_min,
   pipeline_status AS pipeline_status 
FROM staging_trips;


-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: mart_daily_summary
-- Generated Fixes:
--   * No anomalies detected — table copied as-is.
-- =====================================================================

DROP TABLE IF EXISTS cleaned_mart_daily_summary;

CREATE TABLE cleaned_mart_daily_summary AS
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
