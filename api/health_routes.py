"""
CineFluent Health Routes
System health checks and monitoring endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import os

# Import from project root
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import test_connection, supabase

router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    try:
        # Test database connection
        db_status = test_connection()
        
        # Test Supabase auth
        auth_status = True
        try:
            supabase.auth.get_session()
        except Exception:
            auth_status = False
        
        return {
            "status": "healthy" if db_status and auth_status else "degraded",
            "service": "CineFluent API",
            "version": "0.1.0",
            "checks": {
                "database": "ok" if db_status else "error",
                "auth": "ok" if auth_status else "error"
            },
            "environment": {
                "railway_env": os.getenv('RAILWAY_ENVIRONMENT'),
                "service_name": os.getenv('RAILWAY_SERVICE_NAME'),
                "git_commit": os.getenv('RAILWAY_GIT_COMMIT_SHA', 'unknown')[:8]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify deployment"""
    return {
        "message": "CineFluent API is working!",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "environment": os.getenv('RAILWAY_ENVIRONMENT', 'development')
    }

@router.get("/test/database")
async def test_database():
    """Test database connectivity"""
    try:
        response = supabase.table("movies").select("id").limit(1).execute()
        
        return {
            "database": "connected",
            "tables_accessible": True,
            "sample_data": len(response.data) > 0 if response.data else False,
            "message": "Database is working correctly"
        }
    except Exception as e:
        return {
            "database": "error",
            "tables_accessible": False,
            "error": str(e),
            "message": "Database connection failed"
        }
