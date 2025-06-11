# CineFluent API - Streamlined Production Ready

🎬 **Language learning through movies** - FastAPI backend with modular architecture

## Status: ✅ LIVE AND STREAMLINED

- **API URL**: https://cinefluent-api-production.up.railway.app
- **Documentation**: https://cinefluent-api-production.up.railway.app/docs
- **Health Check**: https://cinefluent-api-production.up.railway.app/api/v1/health

## 🚀 What's New

### **Streamlined Architecture**
- **🧩 Modular API**: Routes organized into logical modules (`api/`)
- **🔗 Unified Subtitle Engine**: Consolidated processing pipeline (`core/`)
- **🛠️ Database Manager**: Centralized data operations (`utils/`)
- **📦 Clean Structure**: Clear separation of concerns
- **🗂️ Better Imports**: Proper module organization

### **Enhanced Features**
- ✅ **Modular API Routes** - Better organization and maintainability
- ✅ **Unified Subtitle Processing** - Single comprehensive engine
- ✅ **Centralized Database Operations** - Streamlined data management
- ✅ **Improved Testing Structure** - Essential tests with better coverage
- ✅ **Production Ready** - Optimized for deployment and scaling

## Features

✅ **User Authentication** - JWT-based auth with Supabase  
✅ **Movie Catalog** - Browse and search movies with filtering  
✅ **Subtitle Processing** - Upload and process SRT/VTT files with NLP  
✅ **Progress Tracking** - User learning progress and analytics  
✅ **Interactive Learning** - Vocabulary extraction and quiz generation  

## Tech Stack

- **Framework**: FastAPI (Python) - Modular Architecture
- **Database**: PostgreSQL (Supabase)
- **Authentication**: Supabase Auth + JWT
- **Deployment**: Railway
- **NLP**: spaCy for subtitle processing

## API Endpoints

### 🔐 Authentication (`api/auth_routes.py`)
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### 🎬 Movies (`api/movies_routes.py`)
- `GET /api/v1/movies` - List movies with filtering
- `GET /api/v1/movies/search` - Search movies
- `GET /api/v1/movies/{id}` - Get movie details

### 📊 Progress (`api/progress_routes.py`)
- `POST /api/v1/progress/update` - Update learning progress
- `GET /api/v1/progress/stats` - Get learning statistics

### 📝 Subtitles (`core/subtitle_engine.py`)
- `POST /api/v1/subtitles/upload` - Upload subtitle files
- `GET /api/v1/subtitles/{id}/segments` - Get learning segments

### 🏥 Health (`api/health_routes.py`)
- `GET /api/v1/health` - Detailed health check
- `GET /api/v1/test` - Basic test endpoint

## Quick Start

### **Local Development**
```bash
# Clone and setup
git clone <repository>
cd cinefluent-api

# Install dependencies
pip install -r requirements.txt

# Set environment variables in .env
cp .env.template .env
# Edit .env with your Supabase credentials

# Run locally
python main.py
```

### **Database Management**
```bash
# Get database stats
python -c "from utils.database_manager import DatabaseManager; dm = DatabaseManager(); print(dm.get_database_stats())"

# Populate anime episodes
python -c "from utils.database_manager import DatabaseManager; dm = DatabaseManager(); print(dm.populate_anime_episodes(1))"
```

### **Subtitle Processing**
```bash
# Process subtitles using the unified engine
python -c "from core.subtitle_engine import process_subtitle_file; print('Ready to process subtitles')"
```

## Environment Variables

Required environment variables (set in Railway):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` 
- `SUPABASE_SERVICE_KEY`
- `SUPABASE_JWT_SECRET`
- `DATABASE_URL`

## Frontend Integration

Add to your frontend `.env.local`:
```env
VITE_API_BASE_URL=https://cinefluent-api-production.up.railway.app
VITE_API_VERSION=v1
VITE_ENVIRONMENT=production
```

## Project Structure

```
cinefluent-api/
├── main.py                    # 🔄 Streamlined FastAPI app
├── database.py               # Database configuration
├── auth.py                   # Authentication logic
├── api/                      # 🆕 Modular API routes
│   ├── auth_routes.py        # Authentication endpoints
│   ├── movies_routes.py      # Movie endpoints
│   ├── progress_routes.py    # Progress endpoints
│   └── health_routes.py      # Health endpoints
├── core/                     # 🆕 Core business logic
│   └── subtitle_engine.py    # 🔄 Unified subtitle processing
├── utils/                    # 🆕 Utilities and tools
│   └── database_manager.py   # 🔄 Database operations
├── tests/                    # 🔄 Essential tests
├── subtitles/                # ✅ Content processing
├── docs/                     # ✅ Documentation
└── archive_*/                # 🆕 Archived files (backup)
```

## Database Schema

Complete database schema available in:
- `database/complete_schema.sql` - Full database setup
- `database/subtitle_database_schema.sql` - Subtitle-specific tables

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Test specific modules
python -m pytest tests/test_health.py -v
```

## License

MIT License - see LICENSE file

---

🚀 **CineFluent API - Streamlined & Production Ready** - Empowering language learning through cinema
