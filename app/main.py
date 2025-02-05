from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.models.ranking import init_db
from app.utils.scheduler import RankingScheduler
import logging
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="LANCH Ranking Tracker")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Create scheduler instance
scheduler = RankingScheduler()

@app.on_event("startup")
async def startup_event():
    # Initialize database
    await init_db()
    
    # Start scheduler in background
    asyncio.create_task(scheduler.start())
    logging.info("Ranking scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.stop()
    logging.info("Ranking scheduler stopped") 