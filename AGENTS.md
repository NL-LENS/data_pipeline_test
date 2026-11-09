# AGENTS.md

Working notes for agents contributing to this project.

## General principles

### 1. Verify source files before configuring a dataset

- Dataset names, directory names, and filenames can all differ.
- `lens build bronze --source_regex` matches `source_filename`, not `source_path`.
- Check file availability, filename, reference period, and columns in
  `source_manifest` before adding a source.
- Watch for similarly named sources that a regex could accidentally match.

### 2. Treat the data lake as one stateful system

- Raw data, `lens.duckdb`, bronze, and silver are coupled.
- Cleaning or rebuilding one layer can invalidate metadata used by another.
- Build state and metadata need an explicit invalidation strategy, not just
  deletion of output directories.
- Keep `lens.duckdb` consistent with the bronze files it describes.

### 3. Configure per dataset, not globally

- Regex, reference period, destination, keys, timestamps, and filters differ by
  source.
- Avoid global pipeline settings that force unrelated datasets into the same
  assumptions.
- Prefer structured, explicit source configuration over hidden defaults.

### 4. Settle the data model before implementing silver

- Decide explicitly what is a primary key, secondary key, timestamp, relation,
  or `NOTE` attribute.
- Composite and string identifiers must be represented deliberately.
- Uniqueness assumptions from synthetic data do not automatically hold for real
  data.

### 5. `NOTE` is default-inclusive

- Everything not used as a primary/secondary key and not declared as a
  timestamp belongs in `NOTE`.
- Do not prune columns just because a source is wide.
- Dropping columns is an explicit modeling decision. `RINPERSOONHKW` in `INPA`
  is a deliberate exception.

### 6. Pin and verify the data-pipeline dependency

- The data-pipeline API and behavior can change between commits.
- Know which commit is installed and keep `uv.lock`, the local source, and the
  installed environment consistent.
- Unexpected casting, key, or schema behavior often comes from a version
  change.

### 7. Validate at the database and parquet boundaries

- Check ingested sources, bronze path existence, metadata consistency, silver
  schemas, row counts, date ranges, and null relations.
- Prefer read-only DuckDB checks over rerunning the full pipeline.
- Read-only validation catches issues that command exit codes do not.

### 8. Prototype narrowly and keep an inventory

- Use one year or one file while iterating.
- Maintain `PLAN.md` with available datasets, built layers, blockers, and open
  decisions.
- Do not leave dataset assumptions implicit in conversation or command history.

## Typical workflow

```shell
make init
make bronze
make silver
```

Build one silver event while iterating:

```shell
.venv/bin/python -m data_pipeline_test.make_silver --event GBA_ADDRESS
```

Load silver outputs into DuckDB tables:

```sql
.read load_silver.sql
```
