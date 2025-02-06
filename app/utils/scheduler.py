import asyncio
import logging
from datetime import datetime
from typing import List
from app.services.ranking_service import RankingService
import time

class RankingScheduler:
    def __init__(self):
        self.ranking_service = RankingService()
        self.restaurant_slugs = [
            "loco-chicken-i-frechen",
            "loco-chicken-bielefeld",
            #"happy-slice-suedstadt",
            "happy-slice-pizza-i-wandsbek-markt",
            # Add more restaurants as needed
        ]
        self.interval_minutes = 60
        self.is_running = False
        
    async def start(self):
        """Start the scheduler"""
        self.is_running = True
        logging.info("Starting ranking scheduler...")
        
        while self.is_running:
            start_time = time.time()
            
            try:
                await self.update_all_rankings()
            except Exception as e:
                logging.error(f"Error in scheduler loop: {e}")
            
            # Calculate sleep time
            elapsed_time = time.time() - start_time
            sleep_time = max(0, (self.interval_minutes * 60) - elapsed_time)
            
            logging.info(f"Scheduler sleeping for {sleep_time/60:.2f} minutes")
            await asyncio.sleep(sleep_time)
    
    async def update_all_rankings(self):
        """Update rankings for all restaurants"""
        logging.info(f"Updating rankings at {datetime.now()}")
        
        for slug in self.restaurant_slugs:
            try:
                logging.info(f"Fetching ranking for {slug}")
                ranking_data = await self.ranking_service.get_current_ranking(slug)
                
                if ranking_data:
                    logging.info(f"Successfully updated ranking for {slug}: {ranking_data}")
                else:
                    logging.warning(f"No ranking data found for {slug}")
                
                # Add small delay between requests to avoid overwhelming the target site
                await asyncio.sleep(5)
                
            except Exception as e:
                logging.error(f"Error updating ranking for {slug}: {e}")
                continue
    
    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        logging.info("Stopping ranking scheduler...") 