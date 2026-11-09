-- Load all silver event files into tables.
-- Run from the project root in a DuckDB shell: duckdb

CREATE OR REPLACE TABLE inpa AS
SELECT * FROM read_parquet('data/lake/silver/EVENT=INPA/*.parquet');

CREATE OR REPLACE TABLE job_start AS
SELECT * FROM read_parquet('data/lake/silver/EVENT=JOB_START/*.parquet');

CREATE OR REPLACE TABLE job_end AS
SELECT * FROM read_parquet('data/lake/silver/EVENT=JOB_END/*.parquet');

CREATE OR REPLACE TABLE gba AS
SELECT * FROM read_parquet('data/lake/silver/EVENT=GBA_ADDRESS/*.parquet');

CREATE OR REPLACE TABLE vslgwb AS
SELECT * FROM read_parquet('data/lake/silver/EVENT=VSLGWB_MUNICIPALITY/*.parquet');
