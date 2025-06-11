from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Import our modular routes
from api.auth_routes import router as auth_router
from api.movies_routes import router as movies_router
from api.progress_routes import router as progress_router
from api.health_routes import router as health_router
from api.enhanced_subtitle_routes import router as enhanced_subtitle_router

# Import core functionality
from core.subtitle_engine import SubtitleEngineAPI
from database import test_connection

app.include_router(enhanced_subtitle_router)
app = FastAPI(
    title="CineFluent API", 
    version="0.1.0",
    description="Language learning through movies - Streamlined Architecture"
)

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:19006",
        "https://*.vercel.app",
        "https://*.railway.app",
        "https://*.up.railway.app",
        "https://cinefluent.com",
        "https://www.cinefluent.com",
        "*"  # Allow all for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include all route modules
app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(progress_router)
app.include_router(health_router)

# Include subtitle engine API
subtitle_engine = SubtitleEngineAPI()
app.include_router(subtitle_engine.router)

@app.on_event("startup")
async def startup_event():
    # ... existing startup code ...
    
    # Initialize subtitle service
    try:
        from services.subtitle_fetcher import subtitle_service
        print("✅ Multi-language subtitle service initialized")
    except Exception as e:
        print(f"⚠️ Subtitle service initialization failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    # Clean up subtitle service
    try:
        from services.subtitle_fetcher import subtitle_service
        await subtitle_service.close()
        print("✅ Subtitle service closed")
    except Exception as e:
        print(f"⚠️ Subtitle service cleanup failed: {e}")
        
# Metadata endpoints
@app.get("/api/v1/categories")
async def get_categories():
    """Get all movie categories"""
    from database import supabase
    
    try:
        response = supabase.table("categories").select("*").order("sort_order").execute()
        return {"categories": response.data if response.data else []}
    except Exception:
        # Fallback categories
        fallback_categories = [
            {"id": "action", "name": "Action", "sort_order": 1},
            {"id": "drama", "name": "Drama", "sort_order": 2},
            {"id": "comedy", "name": "Comedy", "sort_order": 3},
            {"id": "thriller", "name": "Thriller", "sort_order": 4},
            {"id": "romance", "name": "Romance", "sort_order": 5},
            {"id": "sci-fi", "name": "Science Fiction", "sort_order": 6},
            {"id": "anime", "name": "Anime", "sort_order": 7}
        ]
        return {"categories": fallback_categories}

@app.get("/api/v1/languages")
async def get_languages():
    """Get all available languages"""
    from database import supabase
    import json
    
    try:
        response = supabase.table("movies").select("languages").execute()
        
        all_languages = set()
        if response.data:
            for movie in response.data:
                languages = movie.get("languages")
                if languages:
                    if isinstance(languages, str):
                        try:
                            languages = json.loads(languages)
                        except:
                            continue
                    if isinstance(languages, list):
                        all_languages.update(languages)
        
        if not all_languages:
            all_languages = {"en", "ja", "es", "fr", "de", "it", "pt", "ru", "ko", "zh"}
        
        return {"languages": sorted(list(all_languages))}
        
    except Exception:
        fallback_languages = ["en", "ja", "es", "fr", "de", "it", "pt", "ru", "ko", "zh"]
        return {"languages": fallback_languages}

# Root endpoint
@app.get("/")
async def root():
    return {
        "status": "healthy", 
        "service": "CineFluent API",
        "version": "0.1.0 - Streamlined",
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'development'),
        "database": "connected" if test_connection() else "disconnected",
        "deployment": "railway",
        "architecture": "modular"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting CineFluent API - Streamlined Version")
    print(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    print(f"Service: {os.getenv('RAILWAY_SERVICE_NAME', 'cinefluent-api')}")
    
    if test_connection():
        print("✅ Database connection established")
    else:
        print("❌ Database connection failed")

# CORS preflight handlers
@app.options("/")
async def options_root():
    return {"message": "OK"}

@app.options("/api/v1/{path:path}")
async def options_api(path: str):
    return {"message": "OK"}

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    print(f"🚀 Starting CineFluent API - Streamlined")
    print(f"📍 Host: {host}:{port}")
    print(f"🌍 Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'development')}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
