"""
Tests for the database price synchronization feature.

Covers:
  - GET /api/sync/price-history  (streaming gzipped CSV export)
  - GET /api/sync/metadata        (JSON export of polling metadata)
"""

import gzip
import io
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from app.utils.database import get_db, engine
from sqlalchemy import text


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _insert_price_history(rows: list[tuple]) -> None:
    """Insert (item_id, timestamp, price_high, price_low, volume_high, volume_low) rows."""
    with engine.connect() as conn:
        conn.execute(
            text(
                "INSERT INTO price_history "
                "(item_id, timestamp, price_high, price_low, volume_high, volume_low) "
                "VALUES (:item_id, :ts, :ph, :pl, :vh, :vl) "
                "ON CONFLICT (item_id, timestamp) DO NOTHING"
            ),
            [
                {"item_id": r[0], "ts": r[1], "ph": r[2], "pl": r[3], "vh": r[4], "vl": r[5]}
                for r in rows
            ],
        )
        conn.commit()


def _clear_price_history() -> None:
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM price_history"))
        conn.commit()


def _decode_gzip_csv(raw_bytes: bytes) -> list[list[str]]:
    """Decompress gzipped CSV bytes and parse into a list of rows."""
    with gzip.GzipFile(fileobj=io.BytesIO(raw_bytes)) as gz:
        text_content = gz.read().decode("utf-8")
    rows = []
    for line in text_content.strip().splitlines():
        if line:
            rows.append(line.split(","))
    return rows


# ─── Tests: /api/sync/price-history ──────────────────────────────────────────

class TestSyncPriceHistoryEndpoint:

    def test_returns_gzip_stream(self, client, synced_items):
        """Endpoint should return a gzipped response."""
        _clear_price_history()
        _insert_price_history([
            (2, datetime(2026, 5, 1, 12, 0, 0), 160, 150, 5000, 4000),
        ])
        response = client.get("/api/sync/price-history")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/gzip"

    def test_all_rows_returned_without_since(self, client, synced_items):
        """Without ?since, all price_history rows are returned."""
        _clear_price_history()
        _insert_price_history([
            (2,    datetime(2026, 5, 1, 10, 0, 0), 160, 150, 5000, 4000),
            (2,    datetime(2026, 5, 1, 11, 0, 0), 162, 151, 5100, 4100),
            (4151, datetime(2026, 5, 1, 10, 0, 0), 1_500_000, 1_480_000, 10, 8),
        ])
        response = client.get("/api/sync/price-history")
        assert response.status_code == 200

        rows = _decode_gzip_csv(response.content)
        assert len(rows) == 3

    def test_since_filter_excludes_old_rows(self, client, synced_items):
        """Rows at or before ?since should not be included."""
        _clear_price_history()
        _insert_price_history([
            (2, datetime(2026, 5, 1, 10, 0, 0), 160, 150, 5000, 4000),  # old
            (2, datetime(2026, 5, 2, 10, 0, 0), 165, 155, 5200, 4200),  # new
        ])
        response = client.get("/api/sync/price-history?since=2026-05-01T10:00:00")
        assert response.status_code == 200

        rows = _decode_gzip_csv(response.content)
        # Only the 2026-05-02 row should appear
        assert len(rows) == 1
        assert "2026-05-02" in rows[0][1]

    def test_empty_result_when_up_to_date(self, client, synced_items):
        """If since is after all data, response should be an empty gzip."""
        _clear_price_history()
        _insert_price_history([
            (2, datetime(2026, 5, 1, 10, 0, 0), 160, 150, 5000, 4000),
        ])
        response = client.get("/api/sync/price-history?since=2026-05-02T00:00:00")
        assert response.status_code == 200

        rows = _decode_gzip_csv(response.content)
        assert rows == []

    def test_csv_columns_correct(self, client, synced_items):
        """Each CSV row should have exactly 6 columns in the right order."""
        _clear_price_history()
        _insert_price_history([
            (2, datetime(2026, 5, 1, 10, 0, 0), 160, 150, 5000, 4000),
        ])
        response = client.get("/api/sync/price-history")
        rows = _decode_gzip_csv(response.content)
        assert len(rows) == 1
        row = rows[0]
        assert len(row) == 6
        # item_id, timestamp, price_high, price_low, volume_high, volume_low
        assert row[0] == "2"
        assert row[2] == "160"
        assert row[3] == "150"
        assert row[4] == "5000"
        assert row[5] == "4000"

    def test_null_prices_represented_as_empty(self, client, synced_items):
        """Null price columns should appear as empty strings in the CSV."""
        _clear_price_history()
        _insert_price_history([
            (2, datetime(2026, 5, 1, 10, 0, 0), None, None, 0, 0),
        ])
        response = client.get("/api/sync/price-history")
        rows = _decode_gzip_csv(response.content)
        assert len(rows) == 1
        assert rows[0][2] == ""  # price_high is null
        assert rows[0][3] == ""  # price_low is null

    def test_invalid_since_format_returns_400(self, client, synced_items):
        """A malformed ?since value should return HTTP 400."""
        response = client.get("/api/sync/price-history?since=not-a-date")
        assert response.status_code == 400


# ─── Tests: /api/sync/metadata ───────────────────────────────────────────────

class TestSyncMetadataEndpoint:

    def test_metadata_returns_200(self, client):
        """Endpoint should respond successfully."""
        response = client.get("/api/sync/metadata")
        assert response.status_code == 200

    def test_metadata_has_required_keys(self, client):
        """Response should include all expected metadata fields."""
        response = client.get("/api/sync/metadata")
        data = response.json()
        for key in ("enabled", "last_poll_timestamp", "last_poll_time",
                    "total_snapshots", "last_item_sync_time"):
            assert key in data, f"Missing key: {key}"

    def test_metadata_enabled_is_bool(self, client):
        response = client.get("/api/sync/metadata")
        data = response.json()
        assert isinstance(data["enabled"], bool)
