"""
Force enable the price polling service in the database.
"""
import logging
from app.utils.database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enable_polling():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE price_polling_metadata SET enabled = TRUE WHERE id = 1")
        conn.commit()
        logger.info("✅ Price polling service forced to ENABLED in database.")

if __name__ == "__main__":
    enable_polling()
