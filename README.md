# Test data lakehouse

This is LLM-generated and used for testing. 
Humans should inspect the resulting silver data base, see instructions at the end.

## Setup

Copy all data from Javier's fake data folder into `data/source`.

## Build

```shell
make init    # scan the raw data into lens.duckdb
make build   # build bronze and silver
```

This writes:

- bronze: `data/lake/bronze/{inpa,spolis,gbaadresobjectbus,vslgwbtab}`
- silver: `data/lake/silver/EVENT=...`

Build one layer at a time:

```shell
make bronze
make silver   # builds bronze first if it has no build stamp yet
```

Bronze builds are tracked with stamps in `data/lake/.stamps`. To force a
bronze rebuild after changing raw data or build settings, remove the bronze
output and its stamps first:

```shell
make clean-bronze
make bronze
```

Clean the generated data:

```shell
make clean          # database + bronze + silver + build stamps
make clean-db       # lens.duckdb + build stamps
make clean-bronze   # data/lake/bronze + build stamps
make clean-silver   # data/lake/silver
```

`make init` only creates the database if it does not exist yet. To recreate it
(and re-scan the source metadata), run:

```shell
make clean-db init
```

Cleaning the database also invalidates the bronze build stamps, so the next
`make build` rebuilds bronze against the new database.

Paths, source names, and per-source reference periods can be overridden. The
period is configured per source in the Makefile, for example:

```shell
make DATA_ROOT=/path/to/data BRONZE_SOURCES="INPA SPOLIS" build
make BRONZE_INPA_PERIOD="2015 2015" bronze
```

## Workflow for humans

```bash
make all
```

Then, in an interactive duckdb shell, 

```sql
.read load_silver.sql
```

or alternatively:

```sql
create table INPA as SELECT * FROM read_parquet('data/lake/silver/EVENT=INPA/');
create table JOB_START as SELECT * FROM read_parquet('data/lake/silver/EVENT=JOB_START/');
create table JOB_END as SELECT * FROM read_parquet('data/lake/silver/EVENT=JOB_END/');
select min(DATE) from INPA;
select max(DATE) from INPA;
select min(DATE) from JOB_START;
select max(DATE) from JOB_END;
```
