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
--   * Replaced NULLs with 0 in column 'delivered_date'
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
   COALESCE(delivered_date, 0) AS delivered_date,
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