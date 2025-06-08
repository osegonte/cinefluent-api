import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print current working directory and check if .env exists
print(f"Current directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Supabase configuration - CLEAN UP WHITESPACE AND NEWLINES
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "").strip()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Debug: Print what we found (without showing secrets)
print(f"SUPABASE_URL loaded: {bool(SUPABASE_URL)}")
print(f"SUPABASE_ANON_KEY loaded: {bool(SUPABASE_ANON_KEY)}")
print(f"SUPABASE_SERVICE_KEY loaded: {bool(SUPABASE_SERVICE_KEY)}")

# Additional debug: Check for hidden characters
if SUPABASE_SERVICE_KEY:
    print(f"🔧 Service key cleaned - length: {len(SUPABASE_SERVICE_KEY)}")

# Only check required vars if we're not in Railway (which sets them differently)
if not all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY]):
    # In Railway, environment variables might be set differently
    # Let's try alternative loading methods
    import subprocess
    railway_env = os.getenv('RAILWAY_ENVIRONMENT')
    
    if railway_env:
        print("🚀 Running in Railway environment")
        # Railway should have set these directly
        if not SUPABASE_URL:
            SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
        if not SUPABASE_ANON_KEY:
            SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
        if not SUPABASE_SERVICE_KEY:
            SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
        if not SUPABASE_JWT_SECRET:
            SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")
        if not DATABASE_URL:
            DATABASE_URL = os.environ.get("DATABASE_URL", "")
            
        print(f"After Railway env check:")
        print(f"SUPABASE_URL: {bool(SUPABASE_URL)}")
        print(f"SUPABASE_ANON_KEY: {bool(SUPABASE_ANON_KEY)}")
        print(f"SUPABASE_SERVICE_KEY: {bool(SUPABASE_SERVICE_KEY)}")
    
    if not all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY]):
        print("❌ Missing required environment variables")
        print("Available env vars:", [k for k in os.environ.keys() if 'SUPABASE' in k or 'DATABASE' in k])
        raise ValueError("Missing required environment variables")

# Only import supabase after we confirm env vars are loaded
try:
    from supabase import create_client, Client
    from sqlalchemy import create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    
    print("✅ Successfully imported Supabase libraries")
    
except ImportError as e:
    print(f"❌ Failed to import libraries: {e}")
    raise

# Create Supabase client with cleaned keys
print(f"🔧 Creating Supabase clients with cleaned credentials...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Create service role client for admin operations
supabase_admin: Client = None
if SUPABASE_SERVICE_KEY:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Admin client created successfully")

# SQLAlchemy setup
engine = None
SessionLocal = None
Base = declarative_base()

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("✅ SQLAlchemy engine created")
    except Exception as e:
        print(f"⚠️ SQLAlchemy setup failed: {e}")

# Dependency to get database session
def get_db():
    if SessionLocal is None:
        raise ValueError("Database not properly configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection
def test_connection():
    try:
        # Test Supabase connection
        result = supabase.table("movies").select("id").limit(1).execute()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False
