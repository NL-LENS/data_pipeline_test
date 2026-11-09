"""Remove column metadata for a source so bronze can be built again."""

from __future__ import annotations

import argparse

import duckdb


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db_file", default="lens.duckdb")
    parser.add_argument("--source_regex", required=True)
    args = parser.parse_args()

    with duckdb.connect(args.db_file) as con:
        table_exists = con.execute(
            """
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_name = 'sav_meta'
            """
        ).fetchone()[0]

        if table_exists:
            con.execute(
                "DELETE FROM sav_meta WHERE source_filename LIKE ?",
                [f"%{args.source_regex}%"],
            )


if __name__ == "__main__":
    main()
