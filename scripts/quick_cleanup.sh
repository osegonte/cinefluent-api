#!/bin/bash

# Quick CineFluent Project Cleanup
# Removes common unused files quickly

set -e

echo "🧹 Quick CineFluent Cleanup"
echo "=========================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REMOVED_COUNT=0
TOTAL_SIZE=0

remove_if_exists() {
    local path="$1"
    local description="$2"
    
    if [[ -e "$path" ]]; then
        local size=$(du -sk "$path" 2>/dev/null | cut -f1 || echo "0")
        rm -rf "$path"
        echo -e "${GREEN}✅ Removed:${NC} $description"
        REMOVED_COUNT=$((REMOVED_COUNT + 1))
        TOTAL_SIZE=$((TOTAL_SIZE + size))
    fi
}

# Python cache files
echo "🐍 Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

# Log files
echo "📝 Cleaning logs..."
remove_if_exists "logs" "Log directory"
find . -name "*.log" -delete 2>/dev/null || true

# Temporary files
echo "🗑️  Cleaning temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*~" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true

# macOS files
echo "🍎 Cleaning macOS files..."
find . -name ".DS_Store" -delete 2>/dev/null || true

# Development caches
echo "🛠️  Cleaning development caches..."
remove_if_exists ".pytest_cache" "Pytest cache"
remove_if_exists ".coverage" "Coverage data"
remove_if_exists "htmlcov" "Coverage reports"
remove_if_exists ".mypy_cache" "MyPy cache"
remove_if_exists ".tox" "Tox environments"

# Subtitle temp files
echo "🎬 Cleaning subtitle cache..."
remove_if_exists "subtitles/temp" "Subtitle temp files"
remove_if_exists "subtitles/.cache" "Subtitle cache"

# Old backups (older than 7 days)
echo "💾 Cleaning old backups..."
find . -name "backup_*" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true

# Railway cache
remove_if_exists ".railway" "Railway cache"

# IDE files
remove_if_exists ".idea" "IntelliJ/PyCharm cache"

echo ""
echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo "Files cleaned: $REMOVED_COUNT"

if [[ $TOTAL_SIZE -gt 0 ]]; then
    if [[ $TOTAL_SIZE -gt 1024 ]]; then
        echo "Space freed: $((TOTAL_SIZE / 1024)) MB"
    else
        echo "Space freed: ${TOTAL_SIZE} KB"
    fi
fi

echo ""
echo "💡 Pro tips:"
echo "• Run 'pip cache purge' to clean pip cache"
echo "• Run 'docker system prune' to clean Docker"
echo "• Use './cleanup_unused_files.sh --dry-run' for detailed cleanup"