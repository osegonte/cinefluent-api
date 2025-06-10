# CineFluent API - Project Structure

## 📁 Production Files

```
cinefluent-api/
├── main.py                 # FastAPI application entry point
├── auth.py                 # Authentication & JWT handling
├── database.py             # Supabase integration & database config
├── subtitle_api.py         # Subtitle processing endpoints
├── subtitle_processor.py   # NLP & subtitle enrichment logic
├── requirements.txt        # Production dependencies
├── requirements-test.txt   # Test dependencies
├── railway.toml           # Railway deployment configuration
├── Procfile               # Process management for Railway
├── Makefile               # Development commands
├── __init__.py            # Python package initialization
├── .gitignore             # Git ignore rules
├── README.md              # Project documentation
├── LICENSE                # MIT License
├── LAUNCH_SUMMARY.md      # Deployment summary
└── PROJECT_STRUCTURE.md   # This file
```

## 📁 Directories

```
tests/                     # Test suite
├── __init__.py
├── conftest.py           # Test configuration
├── test_auth.py          # Authentication tests
├── test_health.py        # Health endpoint tests
└── test_movies.py        # Movie API tests

database/                  # Database schema
├── complete_schema.sql   # Full database setup
└── subtitle_database_schema.sql  # Subtitle tables

scripts/                   # Deployment utilities
└── railway_setup.sh      # Railway environment variables

venv/                     # Virtual environment (local only)
```

## 🚀 Key Commands

```bash
# Development
make run-dev              # Start development server
make test                 # Run test suite
make deploy              # Deploy to Railway

# Production
python main.py           # Start production server
```

## 🌐 Live Deployment

- **API**: https://cinefluent-api-production.up.railway.app
- **Docs**: https://cinefluent-api-production.up.railway.app/docs
- **Health**: https://cinefluent-api-production.up.railway.app/api/v1/health
