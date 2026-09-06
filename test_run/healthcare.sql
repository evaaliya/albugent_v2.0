-- =====================================================================
-- Albugent Autonomous Data Governance: Automated Remediation Script
-- Target Table: raw_patients
-- Generated Fixes:
--   * Fixed invalid/negative age range in column 'age'
--   * Fixed negative values in numeric column 'billing_amount'
--   * Replaced NULLs with 'UNKNOWN' in text column 'name'
--   * Corrected inverted date logic between 'date_of_admission' and 'discharge_date'
--   * Flagged PII columns for governance review: name, medical_condition
-- =====================================================================

DROP TABLE IF EXISTS cleaned_raw_patients;

CREATE TABLE cleaned_raw_patients AS
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
   discharge_date AS discharge_date,
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
--   * Flagged PII columns for governance review: name, medical_condition
-- =====================================================================

DROP TABLE IF EXISTS cleaned_staging_patients;

CREATE TABLE cleaned_staging_patients AS
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
   discharge_date AS discharge_date,
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
--   * Flagged PII columns for governance review: name
-- =====================================================================

DROP TABLE IF EXISTS cleaned_mart_billing;

CREATE TABLE cleaned_mart_billing AS
SELECT 
    COALESCE(name, 'UNKNOWN') AS name,  -- [PII] Contains personally identifiable information
   hospital AS hospital,
   insurance_provider AS insurance_provider,
   admission_type AS admission_type,
   CASE WHEN billing_amount < 0 THEN 0 ELSE billing_amount END AS billing_amount,
   CASE WHEN date_of_admission > discharge_date THEN discharge_date ELSE date_of_admission END AS date_of_admission,
   discharge_date AS discharge_date,
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

DROP TABLE IF EXISTS cleaned_mart_demographics;

CREATE TABLE cleaned_mart_demographics AS
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