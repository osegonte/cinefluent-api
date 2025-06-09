# CineFluent API - Production Ready

🎬 **Language learning through movies** - FastAPI backend deployed on Railway

## Status: ✅ LIVE AND OPERATIONAL

- **API URL**: https://cinefluent-api-production.up.railway.app
- **Documentation**: https://cinefluent-api-production.up.railway.app/docs
- **Health Check**: https://cinefluent-api-production.up.railway.app/api/v1/health

## Features

✅ **User Authentication** - JWT-based auth with Supabase
✅ **Movie Catalog** - Browse and search movies with filtering
✅ **Subtitle Processing** - Upload and process SRT/VTT files with NLP
✅ **Progress Tracking** - User learning progress and analytics
✅ **Interactive Learning** - Vocabulary extraction and quiz generation

## Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (Supabase)
- **Authentication**: Supabase Auth + JWT
- **Deployment**: Railway
- **NLP**: spaCy for subtitle processing

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

### Movies
- `GET /api/v1/movies` - List movies with filtering
- `GET /api/v1/movies/search` - Search movies
- `GET /api/v1/movies/{id}` - Get movie details

### Subtitles & Learning
- `POST /api/v1/subtitles/upload` - Upload subtitle files
- `GET /api/v1/subtitles/{id}/segments` - Get learning segments
- `POST /api/v1/subtitles/segment/{id}/progress` - Update progress

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

## Local Development

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

## Database Schema

Complete database schema available in:
- `database/complete_schema.sql` - Full database setup
- `database/subtitle_database_schema.sql` - Subtitle-specific tables

## License

MIT License - see LICENSE file

---

🚀 **CineFluent API** - Empowering language learning through cinema
