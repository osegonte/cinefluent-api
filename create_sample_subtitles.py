#!/usr/bin/env python3
"""
Create sample subtitle files for testing CineFluent subtitle processing
"""

import os
from pathlib import Path

def create_sample_subtitles():
    """Create sample subtitle files for each anime series"""
    
    # Create directories
    base_dir = Path("subtitles/organized")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample subtitle content for different series
    samples = {
        "my_hero_academia": {
            "content": """1
00:00:01,000 --> 00:00:04,000
Welcome to U.A. High School, the most prestigious hero academy.

2
00:00:04,500 --> 00:00:08,000
My name is Izuku Midoriya, and this is my story.

3
00:00:08,500 --> 00:00:12,000
I want to become the greatest hero, just like All Might.

4
00:00:12,500 --> 00:00:16,000
But there's one problem - I was born without a quirk.

5
00:00:16,500 --> 00:00:20,000
In a world where eighty percent of people have superpowers, I'm ordinary.

6
00:00:20,500 --> 00:00:24,000
Despite this setback, I never gave up on my dream.

7
00:00:24,500 --> 00:00:28,000
Today marks the beginning of my journey to become a hero.
""",
            "difficulty": "beginner"
        },
        
        "jujutsu_kaisen": {
            "content": """1
00:00:01,000 --> 00:00:04,000
Curses are born from human negative emotions.

2
00:00:04,500 --> 00:00:08,000
My name is Yuji Itadori, and I accidentally swallowed a cursed finger.

3
00:00:08,500 --> 00:00:12,000
Now I'm enrolled at Tokyo Jujutsu High School.

4
00:00:12,500 --> 00:00:16,000
Under the guidance of Satoru Gojo, the strongest sorcerer.

5
00:00:16,500 --> 00:00:20,000
I must learn to control the powerful curse within me.

6
00:00:20,500 --> 00:00:24,000
The King of Curses, Ryomen Sukuna, resides in my body.

7
00:00:24,500 --> 00:00:28,000
My mission is to collect all twenty fingers and exorcise him.
""",
            "difficulty": "beginner"
        },
        
        "attack_on_titan": {
            "content": """1
00:00:01,000 --> 00:00:04,000
That day, humanity received a grim reminder.

2
00:00:04,500 --> 00:00:08,000
We lived in fear of the Titans, and were disgraced to live in these cages we called walls.

3
00:00:08,500 --> 00:00:12,000
My name is Eren Yeager, and I witnessed the fall of Wall Maria.

4
00:00:12,500 --> 00:00:16,000
The Colossal Titan appeared out of nowhere, breaching our defenses.

5
00:00:16,500 --> 00:00:20,000
I vowed to eliminate every last Titan from this world.

6
00:00:20,500 --> 00:00:24,000
Joining the Survey Corps was my path to vengeance.

7
00:00:24,500 --> 00:00:28,000
But the truth about Titans was more complex than we imagined.
""",
            "difficulty": "advanced"
        },
        
        "demon_slayer": {
            "content": """1
00:00:01,000 --> 00:00:04,000
My family was attacked by a demon while I was away.

2
00:00:04,500 --> 00:00:08,000
My name is Tanjiro Kamado, and I became a demon slayer.

3
00:00:08,500 --> 00:00:12,000
My sister Nezuko was turned into a demon, but she retained her humanity.

4
00:00:12,500 --> 00:00:16,000
I trained under Sakonji Urokodaki to master Water Breathing techniques.

5
00:00:16,500 --> 00:00:20,000
The Demon Slayer Corps fights to protect humanity from demons.

6
00:00:20,500 --> 00:00:24,000
My enhanced sense of smell helps me track demons effectively.

7
00:00:24,500 --> 00:00:28,000
I seek to find a cure for Nezuko and defeat Muzan Kibutsuji.
""",
            "difficulty": "intermediate"
        }
    }
    
    print("📝 Creating sample subtitle files...")
    
    created_files = []
    
    for series, data in samples.items():
        series_dir = base_dir / series
        series_dir.mkdir(exist_ok=True)
        
        # Create multiple episodes for each series
        for episode in range(1, 4):  # Episodes 1-3
            filename = f"{series}_episode_{episode:02d}_en.srt"
            file_path = series_dir / filename
            
            # Modify content slightly for each episode
            content = data["content"].replace("Episode 1", f"Episode {episode}")
            content = content.replace("00:00:01,000", f"00:00:0{episode},000")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            created_files.append(str(file_path))
            print(f"  ✅ Created: {filename}")
    
    print(f"\n📊 Summary:")
    print(f"  Total files created: {len(created_files)}")
    print(f"  Series covered: {len(samples)}")
    print(f"  Episodes per series: 3")
    
    # Create a Japanese subtitle sample too
    japanese_sample = """1
00:00:01,000 --> 00:00:04,000
僕のヒーローアカデミアへようこそ。

2
00:00:04,500 --> 00:00:08,000
僕の名前は緑谷出久です。

3
00:00:08,500 --> 00:00:12,000
オールマイトのような最高のヒーローになりたいんです。

4
00:00:12,500 --> 00:00:16,000
でも一つ問題があります。僕は無個性で生まれました。

5
00:00:16,500 --> 00:00:20,000
八十パーセントの人が個性を持つ世界で、僕は普通です。
"""
    
    # Add one Japanese subtitle file
    ja_file = base_dir / "my_hero_academia" / "my_hero_academia_episode_01_ja.srt"
    with open(ja_file, 'w', encoding='utf-8') as f:
        f.write(japanese_sample)
    print(f"  ✅ Created: Japanese subtitle sample")
    
    return created_files

def main():
    """Create sample subtitles and show summary"""
    print("🎌 CineFluent - Sample Subtitle Creator")
    print("=" * 40)
    
    files = create_sample_subtitles()
    
    print(f"\n🎯 Next Steps:")
    print(f"  1. Check created files: ls -la subtitles/organized/*/")
    print(f"  2. Test processing: python subtitle_workflow.py process")
    print(f"  3. View results: ls -la subtitles/processed/")
    
    return len(files) > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)