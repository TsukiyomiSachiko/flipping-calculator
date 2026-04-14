from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import items, portfolio, flips, price_history, trajectory, price_history_routes, margin_routes, liquidity, settings, accounts, conversions, auth
from app.utils.database import init_database
from app.services.price_polling_service import price_polling_service
from app.services.data_compression_service import data_compression_service
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app):
    # Initialize database (includes running migrations if needed)
    init_database()
    
    # Start background services
    logger.info("Starting background services...")
    await price_polling_service.start()
    await data_compression_service.start()
    
    yield
    
    # Shutdown: stop services
    logger.info("Shutting down background services...")
    await price_polling_service.stop()
    await data_compression_service.stop()

app = FastAPI(
    title="OSRS Flipping Calculator API",
    description="API for finding profitable OSRS flips and tracking your portfolio",
    version="2.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(items.router, prefix="/api/items", tags=["Items"])
app.include_router(flips.router, prefix="/api/flips", tags=["Flips"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(price_history.router, prefix="/api", tags=["Price History"])
app.include_router(trajectory.router, prefix="/api", tags=["Trajectory"])
app.include_router(price_history_routes.router, prefix="/api", tags=["Price History Storage"])
app.include_router(margin_routes.router, prefix="/api", tags=["Margin Tracking"])
app.include_router(liquidity.router, prefix="/api", tags=["Liquidity Analysis"])
app.include_router(settings.router, prefix="/api", tags=["Settings"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(conversions.router, prefix="/api/conversions", tags=["Conversions"])

@app.get("/")
async def root():
    return {
        "message": "OSRS Flipping Calculator API",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "items": "/api/items",
            "flips": "/api/flips", 
            "portfolio": "/api/portfolio",
            "price_history": "/api/items/{item_id}/price-history",
            "local_price_history": "/api/price-history",
            "polling_stats": "/api/price-history/stats",
            "margin_tracking": "/api/margins/item/{item_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}