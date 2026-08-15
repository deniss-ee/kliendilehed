from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.admin_api.router import admin_router
from app.consumer_api.router import consumer_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Estonian Retail Grocery Price Comparison, Deal Tracker & Basket Optimizer API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration for local Next.js / React back-office & consumer apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
import os

# Mount Routers
app.include_router(admin_router)
app.include_router(consumer_router)

# Mount Local Static Uploads
os.makedirs("./static/uploads", exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory="./static/uploads"), name="static_uploads")

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
