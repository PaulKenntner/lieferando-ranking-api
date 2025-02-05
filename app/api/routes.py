from fastapi import APIRouter, HTTPException
from app.utils.scraper import LieferandoScraper
from app.services.ranking_service import RankingService
import logging
from app.utils.scheduler import RankingScheduler

router = APIRouter()
scraper = LieferandoScraper()
ranking_service = RankingService()

@router.get("/rank/{restaurant_slug}")
async def get_rank(restaurant_slug: str):
    try:
        logging.info(f"Getting rank for restaurant: {restaurant_slug}")
        result = await ranking_service.get_current_ranking(restaurant_slug)
        if result is None:
            logging.warning(f"Restaurant not found: {restaurant_slug}")
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rankings/history/{restaurant_id}")
async def get_ranking_history(restaurant_id: str):
    """Get ranking history for a specific restaurant"""
    try:
        history = await ranking_service.get_ranking_history(restaurant_id)
        return {"restaurant_id": restaurant_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rankings/tracked")
async def get_tracked_rankings():
    """Get latest rankings for all tracked restaurants"""
    try:
        results = []
        for slug in RankingScheduler().restaurant_slugs:
            history = await ranking_service.get_ranking_history(slug)
            if history:
                results.append({
                    "restaurant_slug": slug,
                    "latest_ranking": history[0] if history else None
                })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 