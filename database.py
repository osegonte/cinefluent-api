import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug: Print current working directory and check if .env exists
print(f"Current directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Debug: Print what we found (without showing secrets)
print(f"SUPABASE_URL loaded: {SUPABASE_URL is not None}")
print(f"SUPABASE_ANON_KEY loaded: {SUPABASE_ANON_KEY is not None}")
print(f"DATABASE_URL loaded: {DATABASE_URL is not None}")

if not SUPABASE_URL:
    print("❌ SUPABASE_URL is missing")
if not SUPABASE_ANON_KEY:
    print("❌ SUPABASE_ANON_KEY is missing")
if not DATABASE_URL:
    print("❌ DATABASE_URL is missing")

if not all([SUPABASE_URL, SUPABASE_ANON_KEY]):
    print("\n📝 Please check your .env file contains:")
    print("SUPABASE_URL=https://your-project-id.supabase.co")
    print("SUPABASE_ANON_KEY=eyJ...")
    print("SUPABASE_SERVICE_KEY=eyJ...")
    print("DATABASE_URL=postgresql://...")
    raise ValueError("Missing required environment variables. Check your .env file.")

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

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Create service role client for admin operations (only if service key exists)
supabase_admin: Client = None
if SUPABASE_SERVICE_KEY:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# SQLAlchemy setup for direct database queries (only if DATABASE_URL exists)
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