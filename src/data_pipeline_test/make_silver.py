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
                filter_col={"RINPERSOONS": "R"},
                time_cols=[],
                drop_cols=["RINPERSOONHKW"],
                secondary_keys=None,
                event_time_col=None,
                apply_event_time="01-01",
            ),
        ),
        "JOB_START": (
            "SPOLIS",
            SilverConfig(
                primary_key={"person": "RINPERSOON"},
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
        "VSLGWB_MUNICIPALITY": (
            "VSLGWBTAB",
            SilverConfig(
                primary_key={"dwelling": ["SOORTOBJECTNUMMER", "RINOBJECTNUMMER"]},
                filter_col=None,
                time_cols=[],
                drop_cols=None,
                secondary_keys={"municipality": "GEM2026"},
                event_time_col=None,
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
                dest_path = silver_dir / f"EVENT={event}" / f"{year}.parquet"
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                silver_meta = convert_to_silver(
                        source_manifest=source_manifest,
                        source_path=Path(source_path),
                        source_filename=Path(source_filename),
                        dest_path=dest_path,
                        config=config
                    )

if __name__ == "__main__":
    main()

