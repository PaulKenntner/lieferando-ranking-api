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

    async def get_current_ranking(self, restaurant_slug: str) -> Optional[Dict]:
        """Get current ranking for a restaurant"""
        try:
            ranking_data = await self.scraper.get_ranking(restaurant_slug)
            logging.info(f"Ranking data: {ranking_data}")
            return ranking_data
        except Exception as e:
            logging.error(f"Error getting ranking: {str(e)}")
            return None

    async def get_ranking_history(self, restaurant_slug: str) -> List[dict]:
        """Get ranking history for a restaurant"""
        session = self.SessionLocal()
        try:
            rankings = session.query(Ranking)\
                .filter(Ranking.restaurant_slug == restaurant_slug)\
                .order_by(Ranking.timestamp.desc())\
                .limit(100)\
                .all()
            
            return [{
                'restaurant_slug': r.restaurant_slug,
                'rank': r.rank,
                'rating': r.rating,
                'timestamp': r.timestamp.isoformat()
            } for r in rankings]
        finally:
            session.close()

    async def store_ranking(self, restaurant_slug: str, ranking_data: Dict):
        """Store ranking in database"""
        session = self.SessionLocal()
        try:
            ranking = Ranking(
                restaurant_slug=restaurant_slug,
                rank=ranking_data['rank'],
                rating=ranking_data.get('rating')
            )
            session.add(ranking)
            session.commit()
        except Exception as e:
            session.rollback()
            logging.error(f"Error storing ranking: {str(e)}")
        finally:
            session.close() 