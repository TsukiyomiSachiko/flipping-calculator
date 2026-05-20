import io
import gzip
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from app.utils.database import get_db, engine

router = APIRouter(prefix="/sync", tags=["sync"])

class GzipStreamer:
    def __init__(self, compresslevel=6):
        self.buffer = io.BytesIO()
        self.gzip_file = gzip.GzipFile(mode='wb', fileobj=self.buffer, compresslevel=compresslevel)
    
    def write(self, data: str) -> bytes:
        self.gzip_file.write(data.encode('utf-8'))
        self.gzip_file.flush()
        chunk = self.buffer.getvalue()
        self.buffer.seek(0)
        self.buffer.truncate(0)
        return chunk
        
    def close(self) -> bytes:
        self.gzip_file.close()
        chunk = self.buffer.getvalue()
        self.buffer.seek(0)
        self.buffer.truncate(0)
        return chunk


def csv_generator(since: Optional[datetime]):
    streamer = GzipStreamer()
    raw_conn = engine.raw_connection()
    cursor = None
    try:
        # Named cursors in psycopg2 require a transaction and can only be used server-side
        cursor = raw_conn.cursor(name="sync_price_history_cursor")
        
        if since:
            cursor.execute(
                "SELECT item_id, timestamp, price_high, price_low, volume_high, volume_low "
                "FROM price_history WHERE timestamp > %s ORDER BY timestamp ASC",
                (since,)
            )
        else:
            cursor.execute(
                "SELECT item_id, timestamp, price_high, price_low, volume_high, volume_low "
                "FROM price_history ORDER BY timestamp ASC"
            )
        
        buffer_lines = []
        while True:
            rows = cursor.fetchmany(10000)
            if not rows:
                break
            
            for row in rows:
                item_id = row[0]
                ts_str = row[1].strftime('%Y-%m-%d %H:%M:%S')
                high = row[2] if row[2] is not None else ''
                low = row[3] if row[3] is not None else ''
                v_high = row[4] if row[4] is not None else ''
                v_low = row[5] if row[5] is not None else ''
                line = f"{item_id},{ts_str},{high},{low},{v_high},{v_low}\n"
                buffer_lines.append(line)
                
            if len(buffer_lines) >= 10000:
                chunk = streamer.write("".join(buffer_lines))
                if chunk:
                    yield chunk
                buffer_lines = []
                
        if buffer_lines:
            chunk = streamer.write("".join(buffer_lines))
            if chunk:
                yield chunk
                
        chunk = streamer.close()
        if chunk:
            yield chunk
    except Exception as e:
        raise e
    finally:
        if cursor:
            cursor.close()
        raw_conn.close()


@router.get("/price-history")
async def get_sync_price_history(since: Optional[str] = Query(None, description="ISO timestamp (YYYY-MM-DDTHH:MM:SS)")):
    """
    Export price history as a gzipped CSV stream
    """
    parsed_since = None
    if since:
        try:
            clean_since = since.replace('Z', '').replace('T', ' ')
            try:
                parsed_since = datetime.strptime(clean_since, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                parsed_since = datetime.fromisoformat(since)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid since timestamp format. Use YYYY-MM-DDTHH:MM:SS: {e}")

    try:
        return StreamingResponse(
            csv_generator(parsed_since),
            media_type="application/gzip",
            headers={
                "Content-Disposition": "attachment; filename=price_history.csv.gz"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metadata")
async def get_sync_metadata():
    """
    Get the price polling metadata row
    """
    try:
        with get_db() as session:
            result = session.execute(text(
                "SELECT enabled, last_poll_timestamp, last_poll_time, total_snapshots, last_item_sync_time "
                "FROM price_polling_metadata WHERE id = 1"
            ))
            row = result.fetchone()
            if not row:
                return {
                    "enabled": True,
                    "last_poll_timestamp": None,
                    "last_poll_time": None,
                    "total_snapshots": 0,
                    "last_item_sync_time": None
                }
            return {
                "enabled": row[0],
                "last_poll_timestamp": row[1],
                "last_poll_time": row[2].isoformat() if row[2] else None,
                "total_snapshots": row[3],
                "last_item_sync_time": row[4].isoformat() if row[4] else None
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
