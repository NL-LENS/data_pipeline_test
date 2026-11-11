# Data lake pipeline
#
#   make init           scan raw data into the lens database (if it does not exist)
#   make build          build bronze and silver
#   make bronze         build bronze for sources without a build stamp
#   make silver         build silver from existing bronze
#   make clean          remove the database, bronze, silver and build stamps
#   make clean-db       remove the lens database and build stamps
#   make clean-bronze   remove bronze and its build stamps
#   make clean-silver   remove data/lake/silver
#
# Run `make clean-db init` to recreate the database from scratch. Because the
# database holds the metadata used by bronze, this also invalidates the bronze
# build stamps, so the next `make build` rebuilds bronze.

UV             ?= uv
LENS           ?= $(UV) run lens
PYTHON         ?= $(UV) run python

DB_FILE        ?= lens.duckdb
DATA_ROOT     ?= data/source
LAKE_DIR       ?= data/lake
BRONZE_DIR     ?= $(LAKE_DIR)/bronze
SILVER_DIR     ?= $(LAKE_DIR)/silver
STAMP_DIR      ?= $(LAKE_DIR)/.stamps

BRONZE_SOURCES ?= INPA SPOLIS GBAADRESOBJECTBUS VSLGWBTAB GBAPERSOONTAB KINDOUDERTAB

# lens matches --source_regex against source_filename, not source_path.
BRONZE_INPA_REGEX              := INPA
BRONZE_INPA_PERIOD             := 2015 2020
BRONZE_SPOLIS_REGEX            := SPOLIS
BRONZE_SPOLIS_PERIOD           := 2015 2020
BRONZE_GBAADRESOBJECTBUS_REGEX := GBAADRESOBJECT
BRONZE_GBAADRESOBJECTBUS_PERIOD := 2025 2025
# Use VSLGWB2026 so the regex does not also match NIETVSLGWBTAB202603.
BRONZE_VSLGWBTAB_REGEX         := VSLGWB2026
BRONZE_VSLGWBTAB_PERIOD        := 2026 2026
# Only the latest reference year is needed. The filename regex excludes
# VRLGBAPERSOONTAB and GBAPERSOONLTAB.
BRONZE_GBAPERSOONTAB_REGEX     := GBAPERSOON2025
BRONZE_GBAPERSOONTAB_PERIOD    := 2025 2025
BRONZE_KINDOUDERTAB_REGEX       := KINDOUDER2025TAB
BRONZE_KINDOUDERTAB_PERIOD      := 2025 2025

# NCOBRINVO is not present in data/source yet. Add its regex and period
# here once the source file is available, and add NCOBRINVO to BRONZE_SOURCES.

lower = $(shell printf '%s' '$(1)' | tr '[:upper:]' '[:lower:]')
BRONZE_STAMPS = $(foreach source,$(BRONZE_SOURCES),$(STAMP_DIR)/bronze-$(call lower,$(source)))

.PHONY: all init build bronze silver clean clean-db clean-bronze clean-silver

all: build

init: $(DB_FILE)

$(DB_FILE):
	$(LENS) init --db_file $@ --root $(DATA_ROOT)

build: bronze silver

bronze: $(BRONZE_STAMPS)

# Rebuild a source only when its stamp is missing. Existing column metadata is
# removed first because `lens build bronze` is not idempotent on `sav_meta`.
define BRONZE_RULE
$(STAMP_DIR)/bronze-$(call lower,$(1)): | $(DB_FILE)
	@set -e; \
	mkdir -p "$(STAMP_DIR)"; \
	echo ">>> Building bronze: $(1) -> $(BRONZE_DIR)/$(call lower,$(1))"; \
	$(PYTHON) -m data_pipeline_test.clear_bronze_meta --db_file "$(DB_FILE)" --source_regex "$(BRONZE_$(1)_REGEX)"; \
	$(LENS) build bronze \
		--db_file $(DB_FILE) \
		--source_regex "$(BRONZE_$(1)_REGEX)" \
		--ref_period $(BRONZE_$(1)_PERIOD) \
		--dest_dir "$(BRONZE_DIR)/$(call lower,$(1))"; \
	touch $$@
endef

$(foreach source,$(BRONZE_SOURCES),$(eval $(call BRONZE_RULE,$(source))))

silver: $(DB_FILE) $(BRONZE_STAMPS)
	DB_FILE=$(DB_FILE) SILVER_DIR=$(SILVER_DIR) $(PYTHON) -m data_pipeline_test.make_silver

clean: clean-db clean-bronze clean-silver

clean-db:
	rm -f $(DB_FILE)
	rm -rf $(STAMP_DIR)

clean-bronze:
	rm -rf $(BRONZE_DIR) $(STAMP_DIR)

clean-silver:
	rm -rf $(SILVER_DIR)
