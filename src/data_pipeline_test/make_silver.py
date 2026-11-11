from data_pipeline.silver import convert_to_silver, SilverConfig
from data_pipeline.schemas import SourceManifest
from pathlib import Path
import argparse
import duckdb
from tqdm import tqdm

import logging
import os

logging.basicConfig(level=logging.INFO)

def main():

    db_file = os.environ.get("DB_FILE", "lens.duckdb")
    silver_dir = Path(os.environ.get("SILVER_DIR", "data/lake/silver"))
    source_manifest = SourceManifest(db_file)

    event_dict = {
        "INPA": (
            "INPA",
            SilverConfig(
                primary_key={"person": "RINPERSOON"},
                event_name="INPA",
                filter_col={"RINPERSOONS": "R"},
                drop_cols=["RINPERSOONHKW"],
                apply_event_time="01-01",
            ),
        ),
        "JOB_START": (
            "SPOLIS",
            SilverConfig(
                primary_key={"person": "RINPERSOON"},
                event_name="JOB_START",
                filter_col={"RINPERSOONS": "R"},
                time_cols=[
                    "SDATUMAANVANGIKO",
                    "SDATUMEINDEIKO",
                    "SDATUMAANVANGIKVORG",
                    "SDATUMAANVANGIKV",
                    "SDATUMEINDEIKV",
                ],
                secondary_keys={"job": "IKVID", "company": "SBEID"},
                event_time_col="SDATUMAANVANGIKO",
                event_time_col_fmt="%Y%m%d",
            ),
        ),
        "JOB_END": (
            "SPOLIS",
            SilverConfig(
                primary_key={"person": "RINPERSOON"},
                event_name="JOB_END",
                filter_col={"RINPERSOONS": "R"},
                time_cols=[
                    "SDATUMAANVANGIKO",
                    "SDATUMEINDEIKO",
                    "SDATUMAANVANGIKVORG",
                    "SDATUMAANVANGIKV",
                    "SDATUMEINDEIKV",
                ],
                secondary_keys={"job": "IKVID", "company": "SBEID"},
                event_time_col="SDATUMEINDEIKO",
                event_time_col_fmt="%Y%m%d",
            ),
        ),
        "GBA_ADDRESS": (
            "GBAADRESOBJECTBUS",
            SilverConfig(
                primary_key={"person": "RINPERSOON"},
                event_name="GBA_ADDRESS",
                filter_col={"RINPERSOONS": "R"},
                time_cols=[
                    "GBADATUMAANVANGADRESHOUDING",
                    "GBADATUMEINDEADRESHOUDING",
                ],
                secondary_keys={"dwelling": ["SOORTOBJECTNUMMER", "RINOBJECTNUMMER"]},
                event_time_col="GBADATUMAANVANGADRESHOUDING",
                event_time_col_fmt="%Y%m%d",
            ),
        ),
        "GBA_PERSON": (
            "GBAPERSOONTAB",
            SilverConfig(
                primary_key={"person": "RINPERSOON"},
                event_name="GBA_PERSON",
                filter_col={"RINPERSOONS": "R"},
                apply_event_time="01-01",
            ),
        ),
        # KINDOUDERTAB links a child to the legal father and mother.
        # Keeping the parent pointers as secondary keys (rather than NOTE)
        # preserves the numeric parent IDs; as NOTE attributes they would be
        # classified as continuous and cast to FLOAT, losing leading zeros.
        "KINDOUDER": (
            "KINDOUDERTAB",
            SilverConfig(
                primary_key={"person": "RINPERSOON"},
                event_name="KINDOUDER",
                filter_col={"RINPERSOONS": "R"},
                secondary_keys={
                    "father": ["RINPERSOONSPA", "RINPERSOONPA"],
                    "mother": ["RINPERSOONSMA", "RINPERSOONMA"],
                },
                apply_event_time="01-01",
            ),
        ),
        "VSLGWB_MUNICIPALITY": (
            "VSLGWBTAB",
            SilverConfig(
                primary_key={"dwelling": ["SOORTOBJECTNUMMER", "RINOBJECTNUMMER"]},
                event_name="VSLGWB_MUNICIPALITY",
                secondary_keys={"municipality": "GEM2026"},
                apply_event_time="01-01",
            ),
        ),
    }

    parser = argparse.ArgumentParser(description="Build silver event files.")
    parser.add_argument(
        "--event",
        nargs="+",
        choices=event_dict,
        metavar="EVENT",
        help="Event(s) to build. Defaults to all events.",
    )
    args = parser.parse_args()
    selected_events = args.event or list(event_dict)

    with duckdb.connect(db_file, read_only=True) as con:
        
        con.sql("SET TIMEZONE='UTC'")
        for event in selected_events:
            design, config = event_dict[event]
            sql = f"""
            SELECT source_path, source_filename, ref_period
            FROM '{source_manifest.table_name}'
            WHERE
                ingested_at IS NOT NULL
                AND source_path LIKE ?
            """
            regex_param = f"%{design}%"
            datasets_to_process = con.execute(sql, (regex_param,)).fetchall()
            for source_path, source_filename, ref_period in tqdm(datasets_to_process, desc=f"Creating {event}"):
                year = ref_period.year
                dest_path = silver_dir / config.event_name / f"{year}.parquet"
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                silver_meta = convert_to_silver(
                    source_manifest=source_manifest,
                    source_path=Path(source_path),
                    source_filename=Path(source_filename),
                    dest_path=dest_path,
                    config=config,
                )

if __name__ == "__main__":
    main()

