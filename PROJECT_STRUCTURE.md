# CineFluent Project Structure

## 🎯 Core Application Files
```
├── main.py              # FastAPI application entry point
├── database.py          # Database connection & configuration
├── auth.py              # Authentication & user management
└── requirements.txt     # Python dependencies
```

## 🎌 Anime & Content Management
```
├── anime_db_populator.py    # Populate database with anime episodes
├── subtitle_pipeline.py     # Process subtitle files into learning content
├── subtitle_processor.py    # NLP processing for subtitles
└── subtitle_api.py         # Subtitle-related API endpoints
```

## 🛠️ Tools & Utilities
```
├── tools/
│   ├── anime_manager.py     # Comprehensive anime management
│   └── project_cleanup.py   # Smart project cleanup
└── scripts/
    ├── setup_project.sh     # Project setup automation
    ├── cleanup_unused_files.sh  # Detailed cleanup
    └── quick_cleanup.sh     # Fast cleanup
```

## 📁 Content Directories
```
├── subtitles/
│   ├── organized/           # Organized subtitle files by anime/language
│   │   ├── my_hero_academia/
│   │   ├── demon_slayer/
│   │   ├── jujutsu_kaisen/
│   │   └── attack_on_titan/
│   └── README.md           # Subtitle organization guide
├── database/               # Database schema files
└── docs/                  # Documentation
```

## 🗃️ Archive & Backup
```
├── archive/               # Archived redundant files
├── backups/              # Timestamped backups
└── .venv/                # Python virtual environment
```

## 🚀 Quick Commands

### Setup
```bash
bash scripts/setup_project.sh
```

### Manage Content
```bash
python3 tools/anime_manager.py stats    # Database statistics
python3 tools/anime_manager.py verify   # Verify project structure
```

### Cleanup
```bash
python3 tools/project_cleanup.py        # Quick cleanup
bash scripts/quick_cleanup.sh           # Alternative cleanup
```

### Populate Content
```bash
source .venv/bin/activate
python3 anime_db_populator.py phase1    # Add anime episodes
```

## 📊 Current Status
- ✅ 88 anime episodes populated (4 series)
- ✅ Subtitle directory structure ready
- ✅ Database schema complete
- ✅ API endpoints functional
- 🎯 Ready for subtitle content and frontend integration
