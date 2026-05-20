#!/usr/bin/env python3
"""
sync_from_prod.py — Sync price_history from the production server to the local dev database.

Usage (run inside WSL or the dev docker container):
    python scripts/sync_from_prod.py
    python scripts/sync_from_prod.py --url http://192.168.1.100:3080
    python scripts/sync_from_prod.py --full   # Ignore local max timestamp, re-sync everything

Environment variables:
    PROD_API_URL   URL of the production API (default: https://flipping.tsuki)
    DATABASE_URL   Local PostgreSQL URL (default: same as the API's default)
"""

import os
import sys
import gzip
import csv
import argparse
import logging
import io
from datetime import datetime, timezone

import requests
import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("sync_from_prod")

# ─── Configuration ──────────────────────────────────────────────────────────────

DEFAULT_PROD_URL = os.getenv("PROD_API_URL", "https://flipping.tsuki")
DEFAULT_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://flipping_user:flipping_dev_password@localhost/osrs_flipping",
)

PRICE_HISTORY_ENDPOINT = "/api/sync/price-history"
METADATA_ENDPOINT = "/api/sync/metadata"

# psycopg2 DSN parsed from a postgres:// URL
def parse_dsn(url: str) -> str:
    """Convert a postgresql:// URL to a psycopg2 DSN string."""
    # SQLAlchemy-style URLs work directly with psycopg2 after stripping the driver part.
    # e.g. postgresql+psycopg2://user:pass@host/db → postgresql://user:pass@host/db
    return url.replace("postgresql+psycopg2://", "postgresql://")


# ─── Helpers ────────────────────────────────────────────────────────────────────

def get_local_max_timestamp(conn) -> datetime | None:
    """Return the newest price_history timestamp already in the local DB, or None."""
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(timestamp) FROM price_history;")
        row = cur.fetchone()
        return row[0] if row else None


def stream_price_history(prod_url: str, since: datetime | None) -> requests.Response:
    """Open a streaming GET request to the production sync endpoint."""
    params = {}
    if since:
        params["since"] = since.strftime("%Y-%m-%dT%H:%M:%S")

    url = prod_url.rstrip("/") + PRICE_HISTORY_ENDPOINT
    log.info(f"Connecting to {url}" + (f"  (since {params['since']})" if since else " (full sync)"))

    resp = requests.get(url, params=params, stream=True, timeout=60)
    resp.raise_for_status()
    return resp


def load_price_history(conn, resp: requests.Response) -> int:
    """
    Decompress the gzip stream on the fly, COPY into a staging table,
    then INSERT … ON CONFLICT DO NOTHING into the real table.
    Returns the number of rows inserted.
    """
    with conn.cursor() as cur:
        # Create a temporary staging table that matches price_history (no PK / FK)
        cur.execute("""
            CREATE TEMP TABLE _sync_staging (
                item_id      INTEGER     NOT NULL,
                timestamp    TIMESTAMP   NOT NULL,
                price_high   INTEGER,
                price_low    INTEGER,
                volume_high  INTEGER,
                volume_low   INTEGER
            ) ON COMMIT DROP;
        """)

        # Stream the response → gzip decompress → feed to psycopg2 COPY
        log.info("Streaming and decompressing data into staging table…")
        with gzip.GzipFile(fileobj=resp.raw) as gz:
            # Wrap the binary gzip stream in a text-mode wrapper so psycopg2 can read it
            text_stream = io.TextIOWrapper(gz, encoding="utf-8", newline="")
            cur.copy_expert(
                "COPY _sync_staging (item_id, timestamp, price_high, price_low, volume_high, volume_low) "
                "FROM STDIN WITH (FORMAT csv, NULL '')",
                text_stream,
            )

        cur.execute("SELECT COUNT(*) FROM _sync_staging;")
        staged = cur.fetchone()[0]
        log.info(f"Staged {staged:,} rows — merging into price_history…")

        # Upsert: skip rows that already exist (item_id, timestamp) is the unique key
        cur.execute("""
            INSERT INTO price_history (item_id, timestamp, price_high, price_low, volume_high, volume_low)
            SELECT item_id, timestamp, price_high, price_low, volume_high, volume_low
            FROM   _sync_staging
            ON CONFLICT (item_id, timestamp) DO NOTHING;
        """)
        inserted = cur.rowcount

    conn.commit()
    return inserted


def sync_metadata(conn, prod_url: str) -> None:
    """Fetch metadata JSON from production and upsert it into price_polling_metadata."""
    url = prod_url.rstrip("/") + METADATA_ENDPOINT
    log.info(f"Fetching metadata from {url}…")
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    meta = resp.json()

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO price_polling_metadata
                (id, enabled, last_poll_timestamp, last_poll_time, total_snapshots, last_item_sync_time)
            VALUES (1, %(enabled)s, %(last_poll_timestamp)s, %(last_poll_time)s,
                    %(total_snapshots)s, %(last_item_sync_time)s)
            ON CONFLICT (id) DO UPDATE SET
                enabled             = EXCLUDED.enabled,
                last_poll_timestamp = EXCLUDED.last_poll_timestamp,
                last_poll_time      = EXCLUDED.last_poll_time,
                total_snapshots     = EXCLUDED.total_snapshots,
                last_item_sync_time = EXCLUDED.last_item_sync_time;
        """, {
            "enabled":            meta.get("enabled", True),
            "last_poll_timestamp": meta.get("last_poll_timestamp"),
            "last_poll_time":      meta.get("last_poll_time"),
            "total_snapshots":     meta.get("total_snapshots", 0),
            "last_item_sync_time": meta.get("last_item_sync_time"),
        })
    conn.commit()
    log.info("Metadata synced.")


# ─── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Sync price history from production to local dev DB")
    parser.add_argument("--url",  default=DEFAULT_PROD_URL, help="Production API base URL")
    parser.add_argument("--db",   default=DEFAULT_DB_URL,   help="Local PostgreSQL connection URL")
    parser.add_argument("--full", action="store_true",       help="Ignore local max timestamp and sync everything")
    args = parser.parse_args()

    dsn = parse_dsn(args.db)

    log.info(f"Connecting to local DB: {dsn}")
    try:
        conn = psycopg2.connect(dsn)
    except Exception as e:
        log.error(f"Failed to connect to local database: {e}")
        sys.exit(1)

    try:
        # Step 1: determine how far back we need to go
        since = None
        if not args.full:
            since = get_local_max_timestamp(conn)
            if since:
                log.info(f"Local DB newest record: {since}  — will request records newer than this.")
            else:
                log.info("Local DB has no price history — performing full sync.")

        # Step 2: stream price history from production
        start = datetime.now()
        resp = stream_price_history(args.url, since)
        inserted = load_price_history(conn, resp)
        elapsed = (datetime.now() - start).total_seconds()

        if inserted == 0:
            log.info("Local DB is already up to date — no new rows inserted.")
        else:
            log.info(f"Inserted {inserted:,} new rows in {elapsed:.1f}s.")

        # Step 3: sync metadata
        sync_metadata(conn, args.url)

    except requests.exceptions.ConnectionError as e:
        log.error(f"Could not reach production server at {args.url}: {e}")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        log.error(f"Production server returned an error: {e}")
        sys.exit(1)
    except Exception as e:
        log.exception(f"Unexpected error during sync: {e}")
        sys.exit(1)
    finally:
        conn.close()

    log.info("✅  Sync complete.")


if __name__ == "__main__":
    main()
