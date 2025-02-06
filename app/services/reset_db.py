import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Reset the database and create tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        # Drop existing table if it exists
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS rankings"))
            conn.commit()
            logger.info("Dropped existing rankings table")
        
        # Create new table with correct structure
        create_table_sql = """
        CREATE TABLE rankings (
            id SERIAL PRIMARY KEY,
            restaurant_slug VARCHAR(255) NOT NULL,
            rank INTEGER NOT NULL,
            rating FLOAT,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info("Created new rankings table")
            
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        raise

if __name__ == "__main__":
    reset_database()