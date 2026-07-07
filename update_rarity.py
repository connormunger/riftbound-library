#!/usr/bin/env python3
"""
update_rarity.py — Add and populate a `rarity` column on the cards table
from the Riftbound cache CSV files.

Usage (run from ~/tcg-app on the VM):
    python update_rarity.py --dry-run     # report what WOULD change, write nothing
    python update_rarity.py               # actually apply the update

What it does:
  1. Adds a `rarity TEXT` column to the cards table if it doesn't exist yet.
  2. Reads every data/cache/*.csv, building a riftbound_id -> rarity map.
  3. Updates each cards row by matching on riftbound_id (the unique key).
  4. Reports how many rows were matched, updated, and left unmatched.

Matching is done ONLY on riftbound_id. set_code + collector_number is
deliberately NOT used as a fallback, because those are not unique across
variants (a plain card and its Signature/Overnumbered sibling can share the
same collector_number) — matching on them could assign the wrong rarity.
Rows whose riftbound_id isn't found in the cache are left untouched and
listed at the end for review.

Safe to re-run. A --dry-run is strongly recommended first.
"""

import argparse
import csv
import glob
import os
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(SCRIPT_DIR, "tcg.db")
CACHE_GLOB = os.path.join(SCRIPT_DIR, "data", "cache", "*.csv")

VALID_RARITIES = {"Common", "Uncommon", "Rare", "Epic", "Showcase", "Promo"}


def load_rarity_map():
    """Build {riftbound_id: rarity} from all cache CSVs. Later files win on
    conflict, but conflicts shouldn't happen since riftbound_id is unique."""
    rarity_map = {}
    files = sorted(glob.glob(CACHE_GLOB))
    if not files:
        print(f"No cache files found matching {CACHE_GLOB}")
        sys.exit(1)

    unexpected = set()
    for path in files:
        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(2048)
            f.seek(0)
            delim = "\t" if sample.count("\t") > sample.count(",") else ","
            for row in csv.DictReader(f, delimiter=delim):
                rb = (row.get("riftbound_id") or "").strip()
                rarity = (row.get("rarity") or "").strip()
                if rb and rarity:
                    rarity_map[rb] = rarity
                    if rarity not in VALID_RARITIES:
                        unexpected.add(rarity)

    if unexpected:
        print(f"WARNING: cache contains unexpected rarity values: {sorted(unexpected)}")
        print("These will still be applied, but double-check they're intended.\n")

    print(f"Loaded {len(rarity_map)} riftbound_id -> rarity mappings from {len(files)} cache file(s).")
    return rarity_map


def column_exists(con, table, column):
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})").fetchall()]
    return column in cols


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing anything.")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run this from your ~/tcg-app directory.")
        sys.exit(1)

    rarity_map = load_rarity_map()

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    # 1. Ensure the rarity column exists
    has_col = column_exists(con, "cards", "rarity")
    if not has_col:
        if args.dry_run:
            print("\n[dry-run] Would add column: ALTER TABLE cards ADD COLUMN rarity TEXT")
        else:
            con.execute("ALTER TABLE cards ADD COLUMN rarity TEXT")
            con.commit()
            print("\nAdded column: rarity TEXT")
    else:
        print("\nColumn 'rarity' already exists — will update values in place.")

    # 2. Walk every card row and compute the intended update
    if has_col:
        rows = con.execute(
            "SELECT id, riftbound_id, name, set_code, collector_number, rarity FROM cards"
        ).fetchall()
    else:
        # Column was just added (or would be, in dry-run) — no current value to read
        rows = con.execute(
            "SELECT id, riftbound_id, name, set_code, collector_number FROM cards"
        ).fetchall()
    total = len(rows)

    to_update = []          # (rarity, id)
    already_correct = 0
    unmatched = []          # rows whose riftbound_id isn't in the cache

    for row in rows:
        rb = (row["riftbound_id"] or "").strip()
        new_rarity = rarity_map.get(rb)
        if not rb or new_rarity is None:
            unmatched.append(row)
            continue
        current = row["rarity"] if ("rarity" in row.keys()) else None
        if current == new_rarity:
            already_correct += 1
        else:
            to_update.append((new_rarity, row["id"]))

    # 3. Report
    print(f"\n{'='*55}")
    print(f"Total rows in cards table:   {total}")
    print(f"  Would update / update:     {len(to_update)}")
    print(f"  Already correct:           {already_correct}")
    print(f"  Unmatched (no cache hit):  {len(unmatched)}")
    print(f"{'='*55}")

    if unmatched:
        print(f"\nUnmatched rows (left untouched — riftbound_id not in cache):")
        for row in unmatched[:20]:
            print(f"    {row['name']}  [{row['set_code']}-{row['collector_number']}]  rbid={row['riftbound_id'] or 'MISSING'}")
        if len(unmatched) > 20:
            print(f"    …and {len(unmatched) - 20} more")

    if args.dry_run:
        print("\n[dry-run] No changes written. Re-run without --dry-run to apply.")
        con.close()
        return

    # 4. Apply
    if to_update:
        con.executemany("UPDATE cards SET rarity = ? WHERE id = ?", to_update)
        con.commit()
        print(f"\n✓ Updated rarity on {len(to_update)} row(s).")
    else:
        print("\nNothing to update — all matched rows already correct.")

    con.close()


if __name__ == "__main__":
    main()
