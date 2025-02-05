from app.utils.scraper import LieferandoScraper
from app.models.ranking import Ranking
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.config import settings
from typing import List, Optional, Dict
import logging

class RankingService:
    """Service for handling ranking operations"""
    def __init__(self):
        self.scraper = LieferandoScraper()
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(bind=self.engine)

    async def get_current_ranking(self, restaurant_id: str) -> Optional[Dict]:
        """Get current ranking for a restaurant"""
        try:
            ranking_data = await self.scraper.get_ranking(restaurant_id)
            logging.info(f"Ranking data: {ranking_data}")
            return ranking_data
        except Exception as e:
            logging.error(f"Error getting ranking: {str(e)}")
            return None

    async def get_ranking_history(self, restaurant_id: str) -> List[dict]:
        """Get ranking history for a restaurant"""
        session = self.SessionLocal()
        try:
            rankings = session.query(Ranking)\
                .filter(Ranking.restaurant_id == restaurant_id)\
                .order_by(Ranking.timestamp.desc())\
                .limit(100)\
                .all()
            
            return [{
                'position': r.position,
                'timestamp': r.timestamp.isoformat(),
                'rating': r.rating,
                'review_count': r.review_count,
                'cuisine_types': r.cuisine_types,
                'delivery_time': r.delivery_time,
                'minimum_order': r.minimum_order
            } for r in rankings]
        finally:
            session.close()

    async def store_ranking(self, restaurant_id: str, ranking_data: Dict):
        """Store ranking in database"""
        session = self.SessionLocal()
        try:
            ranking = Ranking(
                restaurant_id=restaurant_id,
                position=ranking_data['rank'],
                name=ranking_data['name'],
                rating=ranking_data.get('rating'),
                review_count=ranking_data.get('review_count'),
                cuisine_types=ranking_data.get('cuisine_types'),
                delivery_time=ranking_data.get('delivery_time'),
                minimum_order=ranking_data.get('minimum_order')
            )
            session.add(ranking)
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error storing ranking: {str(e)}")
        finally:
            session.close() 