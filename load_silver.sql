-- Load all silver event files into tables.
-- Run from the project root in a DuckDB shell: duckdb

CREATE OR REPLACE TABLE inpa AS
SELECT * FROM read_parquet('data/lake/silver/INPA/*.parquet');

CREATE OR REPLACE TABLE job_start AS
SELECT * FROM read_parquet('data/lake/silver/JOB_START/*.parquet');

CREATE OR REPLACE TABLE job_end AS
SELECT * FROM read_parquet('data/lake/silver/JOB_END/*.parquet');

CREATE OR REPLACE TABLE gba_person AS
SELECT * FROM read_parquet('data/lake/silver/GBA_PERSON/*.parquet');

-- RELATIONS.FATHER_ID / RELATIONS.MOTHER_ID: KEY0 is the RINPERSOONS type,
-- KEY1 is the RINPERSOON identifier.
CREATE OR REPLACE TABLE kindouder AS
SELECT * FROM read_parquet('data/lake/silver/KINDOUDER/*.parquet');

CREATE OR REPLACE TABLE vslgwb AS
SELECT * FROM read_parquet('data/lake/silver/VSLGWB_MUNICIPALITY/*.parquet');

CREATE OR REPLACE TABLE gba_address AS
SELECT * FROM read_parquet('data/lake/silver/GBA_ADDRESS/*.parquet');
