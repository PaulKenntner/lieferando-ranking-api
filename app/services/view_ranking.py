import sys
sys.path.append('.')  # Add project root to path

from app.services.ranking_service import RankingService
from datetime import datetime, timedelta
import logging

def format_rankings(rankings):
    """Format rankings for display"""
    print(f"\nRankings:")
    print("=" * 80)
    print(f"{'Timestamp':<25} {'Restaurant':<35} {'Rank':<6} {'Rating':<6}")
    print("-" * 80)
    
    for r in rankings:
        print(f"{datetime.fromisoformat(r['timestamp']).strftime('%Y-%m-%d %H:%M:%S'):<25} "
              f"{r['restaurant_slug']:<35} "
              f"{r['rank']:<6} "
              f"{r['rating'] if r['rating'] else 'N/A':<6}")
    
    print("=" * 80)
    print(f"Total entries: {len(rankings)}")

async def view_rankings(restaurant_slug: str = None, days: int = 7):
    """View rankings using the RankingService"""
    service = RankingService()
    try:
        # Use the service method to get rankings
        rankings = await service.get_ranking_history(restaurant_slug, limit=days * 24)  # Assuming hourly rankings
        if rankings:
            format_rankings(rankings)
        else:
            print(f"No rankings found{f' for {restaurant_slug}' if restaurant_slug else ''}")
    except Exception as e:
        logging.error(f"Error viewing rankings: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    import asyncio
    
    parser = argparse.ArgumentParser(description='View restaurant rankings')
    parser.add_argument('--slug', type=str, help='Restaurant slug to filter by')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back')
    
    args = parser.parse_args()
    
    # Run the async function
    asyncio.run(view_rankings(args.slug, args.days))