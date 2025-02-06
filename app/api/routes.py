from fastapi import APIRouter, HTTPException
from app.services.ranking_service import RankingService
import logging

router = APIRouter()
ranking_service = RankingService()

@router.get("/rank/{restaurant_slug}")
async def get_rank(restaurant_slug: str):
    """Get current ranking for a restaurant"""
    try:
        result = await ranking_service.get_current_ranking(restaurant_slug)
        if result is None:
            raise HTTPException(status_code=404, detail="Restaurant not found or currently closed")
        return result
    except Exception as e:
        logging.error(f"Error getting rank for {restaurant_slug}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))