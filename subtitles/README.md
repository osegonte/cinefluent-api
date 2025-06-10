# CineFluent Subtitle Organization Guide

## Directory Structure
subtitles/
├── organized/
│   ├── my_hero_academia/
│   │   ├── en/          # English subtitles
│   │   ├── ja/          # Japanese subtitles
│   │   └── es/          # Spanish subtitles
│   ├── demon_slayer/
│   │   ├── en/
│   │   ├── ja/
│   │   ├── es/
│   │   └── fr/          # French subtitles
│   ├── jujutsu_kaisen/
│   │   ├── en/
│   │   ├── ja/
│   │   └── es/
│   └── attack_on_titan/
│       ├── en/
│       ├── ja/
│       ├── es/
│       ├── fr/
│       └── de/          # German subtitles
└── sample_structure/    # Example structure

## File Naming Convention
Place subtitle files with clear naming:
- `Episode_01_English.srt`
- `Episode_01_Japanese.srt`
- `E01_EN.srt`
- `01.en.srt`

## Supported Formats
- .srt (SubRip) - Most common
- .vtt (WebVTT) - Web standard
- .ass (Advanced SubStation Alpha) - Advanced formatting
- .ssa (SubStation Alpha) - Legacy format

## Supported Languages
- en (English)
- ja (Japanese) 
- es (Spanish)
- fr (French)
- de (German)
- pt (Portuguese)
- it (Italian)
- ko (Korean)
- zh (Chinese)

## How to Use
1. Download subtitle files for your target anime
2. Place them in the appropriate language directories
3. Use consistent naming (episode number + language)
4. Run processing when ready

## Popular Subtitle Sources
- OpenSubtitles.org (legal, community-driven)
- Subscene.com (high quality)
- Kitsunekko.net (Japanese anime subtitles)
- Anime streaming platforms (official)

## Next Steps
1. Populate the directories with subtitle files
2. Run: `python3 anime_db_populator.py phase1` (to add episodes first)
3. Then process subtitles through the learning pipeline

## Tips
- Start with English subtitles (easiest to find)
- Japanese subtitles are great for advanced learners
- Multiple languages help with translation practice
- Check file encoding (UTF-8 preferred)
