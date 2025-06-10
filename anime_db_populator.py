#!/usr/bin/env python3
"""
CineFluent Anime Database Population Script
Populates the backend with 8 popular anime series for language learning
"""

import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import os
import random
from dataclasses import dataclass

# Database connection (using your existing setup)
try:
    import sys
    import os
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    from database import supabase, supabase_admin
    print("✅ Connected to Supabase with admin access")
except ImportError as e:
    print(f"❌ Could not import database: {e}")
    print("Available files in directory:")
    try:
        import os
        files = [f for f in os.listdir('.') if f.endswith('.py')]
        for file in files:
            print(f"  - {file}")
    except:
        pass
    print("\nTrying alternative import...")
    
    # Try alternative approach
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("database", "./database.py")
        database_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(database_module)
        supabase = database_module.supabase
        supabase_admin = getattr(database_module, 'supabase_admin', supabase)
        print("✅ Successfully imported database using alternative method")
    except Exception as e2:
        print(f"❌ Alternative import also failed: {e2}")
        print("Please ensure you have database.py in the current directory and run:")
        print("python3 -c \"from database import supabase; print('Database import works')\"")
        exit(1)

@dataclass
class AnimeEpisode:
    """Represents a single anime episode"""
    title: str
    description: str
    duration: int  # minutes
    release_year: int
    difficulty_level: str
    languages: List[str]
    genres: List[str]
    thumbnail_url: str
    video_url: str
    is_premium: bool
    vocabulary_count: int
    imdb_rating: float
    series_name: str
    episode_number: int
    season_number: int
    total_episodes_in_season: int

class AnimeDBPopulator:
    """Populates the CineFluent database with anime content"""
    
    def __init__(self):
        self.anime_series = self._define_anime_series()
        self.total_episodes_added = 0
        
    def _define_anime_series(self) -> Dict[str, Dict]:
        """Define the 8 target anime series with metadata"""
        return {
            "my_hero_academia": {
                "name": "My Hero Academia",
                "japanese_name": "Boku no Hero Academia",
                "season": 1,
                "total_episodes": 13,
                "difficulty": "beginner",
                "release_year": 2016,
                "genres": ["anime", "action", "school", "superhero"],
                "description_template": "In a world where superpowers called 'Quirks' are the norm, Izuku Midoriya dreams of becoming a hero despite being born without powers.",
                "base_imdb_rating": 8.7,
                "vocabulary_range": (300, 450),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BNTc0YmJkMTQtYjU0MS00NmM5LWJjMDUtZGQzMzRkNzM1ZjIzXkEyXkFqcGdeQXVyMzI2Mzc4OTY@._V1_.jpg",
                "video_base": "https://example.com/mha/s1",
                "is_premium": False
            },
            "demon_slayer": {
                "name": "Demon Slayer",
                "japanese_name": "Kimetsu no Yaiba",
                "season": 1,
                "total_episodes": 26,
                "difficulty": "intermediate",
                "release_year": 2019,
                "genres": ["anime", "action", "supernatural", "historical"],
                "description_template": "Tanjiro Kamado becomes a demon slayer to save his sister Nezuko and avenge his family.",
                "base_imdb_rating": 8.9,
                "vocabulary_range": (450, 600),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BZjZjNzI5MDctY2Y4YS00NmM4LWJjMjUtMGJjNzhkMzA5NTI1XkEyXkFqcGdeQXVyNjc3MjQzNTI@._V1_.jpg",
                "video_base": "https://example.com/demon-slayer/s1",
                "is_premium": False
            },
            "jujutsu_kaisen": {
                "name": "Jujutsu Kaisen",
                "japanese_name": "Jujutsu Kaisen",
                "season": 1,
                "total_episodes": 24,
                "difficulty": "beginner",
                "release_year": 2020,
                "genres": ["anime", "action", "supernatural", "school"],
                "description_template": "Yuji Itadori joins a secret organization of sorcerers to eliminate cursed spirits and find the remaining fingers of a powerful curse.",
                "base_imdb_rating": 8.8,
                "vocabulary_range": (350, 500),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BNjcyMjg0MjQtMDRjMC00NzI3LWE4MDQtYTVkN2RmODMxMDIwXkEyXkFqcGdeQXVyMTA4NjE0NjEy._V1_.jpg",
                "video_base": "https://example.com/jujutsu-kaisen/s1",
                "is_premium": False
            },
            "attack_on_titan": {
                "name": "Attack on Titan",
                "japanese_name": "Shingeki no Kyojin",
                "season": 1,
                "total_episodes": 25,
                "difficulty": "advanced",
                "release_year": 2013,
                "genres": ["anime", "action", "drama", "thriller"],
                "description_template": "Humanity fights for survival against giant humanoid Titans that threaten their existence.",
                "base_imdb_rating": 9.0,
                "vocabulary_range": (650, 800),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BNzUxNDU5NTItNDJhZi00NjlkLTlkY2YtNDBhM2E3YTY5ZjNmXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
                "video_base": "https://example.com/attack-on-titan/s1",
                "is_premium": True
            },
            "death_note": {
                "name": "Death Note",
                "japanese_name": "Death Note",
                "season": 1,
                "total_episodes": 37,
                "difficulty": "advanced",
                "release_year": 2006,
                "genres": ["anime", "thriller", "supernatural", "psychological"],
                "description_template": "Light Yagami discovers a supernatural notebook that can kill anyone whose name is written in it.",
                "base_imdb_rating": 9.0,
                "vocabulary_range": (700, 850),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BNjRiNmNjMmMtN2U2Yi00ODgxLTk3OTMtMmI1MTI1NjYyZTEzXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
                "video_base": "https://example.com/death-note/s1",
                "is_premium": True
            },
            "dragon_ball_z": {
                "name": "Dragon Ball Z",
                "japanese_name": "Dragon Ball Z",
                "season": 1,
                "total_episodes": 39,  # Saiyan Saga
                "difficulty": "beginner",
                "release_year": 1989,
                "genres": ["anime", "action", "adventure", "martial-arts"],
                "description_template": "Goku and the Z fighters protect Earth from powerful alien threats and discover Goku's Saiyan heritage.",
                "base_imdb_rating": 8.8,
                "vocabulary_range": (250, 400),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BMGU5NzFjNzQtMGJiYS00NjQzLTgzOWEtNTJhZjY4YTAwOWFjXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
                "video_base": "https://example.com/dragon-ball-z/s1",
                "is_premium": False
            },
            "one_piece": {
                "name": "One Piece",
                "japanese_name": "One Piece",
                "season": 1,
                "total_episodes": 61,  # East Blue Saga
                "difficulty": "intermediate",
                "release_year": 1999,
                "genres": ["anime", "action", "adventure", "comedy"],
                "description_template": "Monkey D. Luffy and his Straw Hat Pirates search for the ultimate treasure 'One Piece' to become the Pirate King.",
                "base_imdb_rating": 8.9,
                "vocabulary_range": (500, 650),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BOThjZGJjODYtOWYwYS00NGJhLWI1OWEtOGQ5MTFjYWMyOGU3XkEyXkFqcGdeQXVyMTA4NjE0NjEy._V1_.jpg",
                "video_base": "https://example.com/one-piece/s1",
                "is_premium": False
            },
            "naruto": {
                "name": "Naruto",
                "japanese_name": "Naruto",
                "season": 1,
                "total_episodes": 220,
                "difficulty": "intermediate",
                "release_year": 2002,
                "genres": ["anime", "action", "adventure", "martial-arts"],
                "description_template": "Naruto Uzumaki, a young ninja, seeks recognition and dreams of becoming the leader of his village.",
                "base_imdb_rating": 8.3,
                "vocabulary_range": (450, 600),
                "thumbnail_base": "https://m.media-amazon.com/images/M/MV5BZmNjZGJjMGItNTY1OC00MGI4LWJlZWItMDU0YjFlMmI2MjhhXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg",
                "video_base": "https://example.com/naruto/s1",
                "is_premium": False
            }
        }
    
    def generate_episode_title(self, series_key: str, episode_num: int) -> str:
        """Generate episode title based on series and episode number"""
        series = self.anime_series[series_key]
        
        # Episode title patterns for each series
        title_patterns = {
            "my_hero_academia": [
                "Izuku Midoriya: Origin", "What It Takes to Be a Hero", "Roaring Muscles",
                "Start Line", "What I Can Do for Now", "Rage, You Damn Nerd",
                "Deku vs Kacchan", "Bakugo's Start Line", "Yeah, Just Do Your Best, Ida!",
                "Encounter with the Unknown", "Game Over", "All Might", "In Each of Our Hearts"
            ],
            "demon_slayer": [
                "Cruelty", "Trainer Sakonji Urokodaki", "Sabito and Makomo",
                "Final Selection", "My Own Steel", "Swordsman Accompanying a Demon",
                "Muzan Kibutsuji", "The Smell of Enchanting Blood", "Temari Demon and Arrow Demon",
                "Together Forever", "Tsuzumi Mansion", "The Boar Bares Its Fangs, Zenitsu Sleeps",
                "Something More Important Than Life", "The House with the Wisteria Family Crest",
                "Mount Natagumo", "Letting Someone Else Go First", "You Must Master a Single Thing",
                "A Forged Bond", "Hinokami", "Pretending to Be Asleep", "Against Corps Rules",
                "Master of the Mansion", "Hashira Meeting", "Rehabilitation Training", "New Mission", "The Butterfly Mansion"
            ],
            "jujutsu_kaisen": [
                "Ryomen Sukuna", "For Myself", "Girl of Steel", "Curse Womb Must Die",
                "Curse Womb Must Die -II-", "After Rain", "Assault", "Boredom",
                "Small Fry and Reverse Retribution", "Idle Transfiguration", "Narrow-minded",
                "To You, Someday", "Tomorrow", "Kyoto Sister School Exchange Event - Group Battle 0 -",
                "Kyoto Sister School Exchange Event - Group Battle 1 -", "Kyoto Sister School Exchange Event - Group Battle 2 -",
                "Kyoto Sister School Exchange Event - Group Battle 3 -", "Sage", "Black Flash",
                "Nonstandard", "Jujutsu Koshien", "The Origin of Blind Obedience", "The Origin of Blind Obedience -II-", "Accomplices"
            ],
            "attack_on_titan": [
                "To You, in 2000 Years: The Fall of Shiganshina, Part 1", "That Day: The Fall of Shiganshina, Part 2",
                "A Dim Light Amid Despair: Humanity's Comeback, Part 1", "The Night of the Closing Ceremony: Humanity's Comeback, Part 2",
                "First Battle: The Struggle for Trost, Part 1", "The World the Girl Saw: The Struggle for Trost, Part 2",
                "Small Blade: The Struggle for Trost, Part 3", "I Can Hear His Heartbeat: The Struggle for Trost, Part 4",
                "Whereabouts of His Left Arm: The Struggle for Trost, Part 5", "Response: The Struggle for Trost, Part 6",
                "Idol: The Struggle for Trost, Part 7", "Wound: The Struggle for Trost, Part 8",
                "Primal Desire: The Struggle for Trost, Part 9", "Can't Look into His Eyes Yet: Eve of the Counterattack, Part 1",
                "Special Operations Squad: Eve of the Counterattack, Part 2", "What Needs to be Done Now: Eve of the Counterattack, Part 3",
                "Female Titan: The 57th Exterior Scouting Mission, Part 1", "Forest of Giant Trees: The 57th Exterior Scouting Mission, Part 2",
                "Bite: The 57th Exterior Scouting Mission, Part 3", "Erwin Smith: The 57th Exterior Scouting Mission, Part 4",
                "Crushing Blow: The 57th Exterior Scouting Mission, Part 5", "The Defeated: The 57th Exterior Scouting Mission, Part 6",
                "Smile: Assault on Stohess, Part 1", "Mercy: Assault on Stohess, Part 2", "Wall: Assault on Stohess, Part 3"
            ],
            "death_note": [
                "Rebirth", "Confrontation", "Dealings", "Pursuit", "Tactics", "Unraveling",
                "Overcast", "Glare", "Encounter", "Doubt", "Assault", "Love", "Confession",
                "Friend", "Wager", "Decision", "Execution", "Ally", "Matsuda", "Makeshift",
                "Performance", "Guidance", "Frenzy", "Revival", "Silence", "Renewal",
                "Abduction", "Scream", "Judgment", "Justice", "Transfer", "Selection",
                "Scorn", "Vigilance", "Inferno", "1.28", "New World"
            ],
            "dragon_ball_z": [
                "The New Threat", "Reunions", "Unlikely Alliance", "Piccolo's Plan",
                "Gohan's Rage", "No Time Like the Present", "Day 1", "Gohan Goes Bananas!",
                "The Strangest Robot", "A New Friend", "Terror on Arlia", "Global Training",
                "Goz and Mez", "Princess Snake", "Dueling Piccolos", "Plight of the Children",
                "Pendulum Room Peril", "The End of Snake Way", "Defying Gravity",
                "Goku's Ancestors", "Counting Down", "The Darkest Day", "Saibamen Attack!",
                "The Power of Nappa", "Sacrifice", "Nappa's Rampage", "Nimbus Speed",
                "Goku's Arrival", "Lesson Number One", "Goku vs. Vegeta", "Saiyan Sized Secret",
                "Spirit Bomb Away!", "Hero in the Shadows", "Krillin's Offensive", "Mercy",
                "Picking Up the Pieces", "Plans for Departure", "Nursing Wounds", "Friends or Foes?"
            ],
            "one_piece": [
                "I'm Luffy! The Man Who's Gonna Be King of the Pirates!", "Enter the Great Swordsman! Pirate Hunter Roronoa Zoro!",
                "Morgan versus Luffy! Who's the Mysterious Pretty Girl?", "Luffy's Past! Enter Red-Haired Shanks!",
                "Fear, Mysterious Power! Pirate Clown Captain Buggy!", "Desperate Situation! Beast Tamer Mohji vs. Luffy!",
                "Epic Showdown! Swordsman Zoro vs. Acrobat Cabaji!", "Who Will Win? Showdown Between the True Powers of the Devil Fruit!",
                "The Honorable Liar? Captain Usopp!", "The Weirdest Guy Ever! Jango the Hypnotist!",
                "Expose the Plot! Pirate Butler, Captain Kuro!", "Clash with the Black Cat Pirates! The Great Battle on the Slope!",
                "The Terror, the Trio of Baddies! Captain Kuro's Secret Plan!", "Luffy Back in Action! Miss Kaya's Desperate Resistance!",
                "Beat Kuro! Usopp the Man's Tearful Resolve!", "Protect Kaya! The Usopp Pirates' Great Efforts!",
                "Anger Explosion! Kuro vs. Luffy! How It Ends!", "You're the Weird Creature! Gaimon and His Strange Friends!",
                "The Three-Sword Style's Past! Zoro and Kuina's Vow!", "Famous Cook! Sanji of the Sea Restaurant!",
                "Unwelcome Customer! Sanji's Food and Ghin's Debt!", "The Strongest Pirate Fleet! Commodore Don Krieg!",
                "Protect Baratie! The Great Pirate, Red Foot Zeff!", "Hawk-Eye Mihawk! The Great Swordsman Zoro Falls At Sea!",
                "The Deadly Foot Technique Bursts Forth! Sanji vs. the Invincible Pearl!", "Zeff and Sanji's Dream! The Illusory All Blue!",
                "Cool-headed, Cold-hearted Demon! Pirate Fleet Chief Commander Ghin!", "I Won't Die! Fierce Battle, Luffy vs. Krieg!",
                "The Conclusion of the Deadly Battle! A Spear of Blind Determination!", "The Cooks' Goodbye! Sanji and the Straw Hat Crew!",
                "Usopp's Return Home! Captain Kuro's Conspiracy!", "The Weirdest Guy Ever! Jango the Hypnotist!",
                "Arlong Park! The Worst in the East Blue!", "The Witch of Cocoyasi Village! Arlong's Female Officer!",
                "Usopp's Death?! Luffy - Yet to Land?", "The Hidden Past! Female Fighter Bellemere!",
                "Survive! Mother Bellemere and Nami's Family!", "Luffy Rises! Result of the Broken Promise!",
                "Luffy in Trouble! Fishmen vs. Luffy Pirates!", "Luffy Submerged! Zoro vs. Hatchan the Octopus!",
                "Proud Warriors! Sanji and Usopp's Fierce Battles!", "Luffy's Best! Nami's Courage and the Straw Hat!",
                "Bursting Out! Fishman Arlong! Luffy vs. Arlong!", "The End of the Fishman Empire! Nami's My Friend!",
                "Setting Off with a Smile! Farewell, Hometown Cocoyasi Village!", "Bounty! Straw Hat Luffy Becomes Known to the World!",
                "Following the Straw Hat! Little Buggy's Big Adventure!", "Angry Finale! Cross the Red Line!",
                "The First Patient! The Untold Story of the Rumble Ball!", "Hiriluk's Cherry Blossoms and Inherited Will!",
                "Dalton's Resolve! Wapol's Forces Land!", "Devil's Fruit of the Zoan Family! Chopper's Seven-Form Transformation!",
                "When the Kingdom's Rule is Over! The Flag of Faith Flies Forever!", "Hiruluk's Cherry Blossoms! Miracle in the Drum Kingdom!",
                "Farewell, Drum Island! I'm Going Out to Sea!", "The Hero of Alabasta and the Ballerina on Deck!",
                "Coming to the Desert Kingdom! The Rain-Calling Powder and the Rebel Army!", "Reunion of the Powerful! His Name is Fire Fist Ace!",
                "Ace and Luffy! Hot Emotions and Brotherly Bonds!", "The Green City, Erumalu and the Kung Fu Dugongs!",
                "Adventure in the Country of Sand! The Demons that Live in the Scorching Earth!", "Here Come the Desert Pirates! The Men Who Live Free!",
                "False Fortitude! Camu, Rebel Soldier at Heart!", "Rebellion of the Sand! Koza, Warrior of Hope!",
                "Alubarna Grieves! The Fierce Captain Karoo!", "Magnificent Wings! My Name is Pell, Guardian Spirit of the Kingdom!"
            ],
            "naruto": [
                "Enter: Naruto Uzumaki!", "My Name is Konohamaru!", "Sasuke and Sakura: Friends or Foes?",
                "Pass or Fail: Survival Test", "You Failed! Kakashi's Final Decision", "A Dangerous Mission! Journey to the Land of Waves!",
                "The Assassin of the Mist!", "The Oath of Pain", "Kakashi: Sharingan Warrior!",
                "The Forest of Chakra", "The Land Where a Hero Once Lived", "Battle on the Bridge! Zabuza Returns!",
                "Haku's Secret Jutsu: Crystal Ice Mirrors!", "The Number One Hyperactive, Knucklehead Ninja Joins the Fight!",
                "Zero Visibility: The Sharingan Shatters!", "The Broken Seal", "White Past: Hidden Ambition",
                "The Weapons Known as Shinobi", "The Demon in the Snow", "A New Chapter Begins: The Chunin Exam!",
                "Identify Yourself: Powerful New Rivals!", "Chunin Challenge: Rock Lee vs. Sasuke!",
                "Genin Takedown! All Nine Rookies Face Off!", "Start Your Engines: The Chunin Exam Begins!",
                "The Tenth Question: All or Nothing!", "Special Report: Live from the Forest of Death!",
                "The Chunin Exam Stage 2: The Forest of Death", "Eat or be Eaten: Panic in the Forest!",
                "Naruto's Counterattack: Never Give In!", "The Sharingan Revived: Dragon Flame Jutsu!",
                "The Dancing Leaf, the Squirming Sand", "Bushy Brow's Jealousy: Lions Barrage Unleashed!",
                "Assassination Plot! The Bloodthirsty Orochimaru!", "The Scroll's Secret: No Peeking Allowed",
                "Surviving the Cut! The Rookie Nine Together Again!", "Clone vs. Clone: Mine are Better than Yours!",
                "Surviving the Cut! The Rookie Nine Together Again!", "Formation! The Sasuke Recovery Team!",
                "Miscalculation: A New Enemy Appears!", "Dancing Shadows: The Impersonation Shuriken Technique!",
                "The Beast Within", "Kunoichi Rumble: The Rivals Get Serious!", "Ultimate Defense: Zero Blind Spot!",
                "The Leaf's Handsome Devil!", "Killer Kunoichi and a Shaky Shikamaru!", "Akamaru Unleashed! Who's Top Dog Now?",
                "Howling Success: The Combination Jutsu!", "Return of the Morning Mist!", "The Fifth Hokage! A Life on the Line!",
                "A Dubious Offer! Tsunade's Choice!", "Sannin Showdown! Jiraiya vs. Orochimaru!"
            ]
        }
        
        patterns = title_patterns.get(series_key, [])
        if episode_num <= len(patterns):
            return f"{series['name']} - Episode {episode_num}: {patterns[episode_num - 1]}"
        else:
            return f"{series['name']} - Episode {episode_num}: The Adventure Continues"
    
    def generate_episode_description(self, series_key: str, episode_num: int) -> str:
        """Generate episode description"""
        series = self.anime_series[series_key]
        base_desc = series['description_template']
        
        # Add episode-specific details
        episode_descriptions = {
            1: f"The series begins as {base_desc} Episode 1 introduces the main characters and sets the stage.",
            2: f"Building on the foundation, {base_desc} The story deepens with new challenges.",
            3: f"The adventure continues as {base_desc} Character development takes center stage."
        }
        
        if episode_num in episode_descriptions:
            return episode_descriptions[episode_num]
        else:
            return f"{base_desc} Episode {episode_num} continues the epic journey with new challenges and discoveries."
    
    def calculate_episode_rating(self, series_key: str, episode_num: int, total_episodes: int) -> float:
        """Calculate episode rating with variation"""
        base_rating = self.anime_series[series_key]['base_imdb_rating']
        
        # Add variation: first and last episodes tend to be higher rated
        if episode_num == 1:
            variation = random.uniform(0.1, 0.3)
        elif episode_num == total_episodes:
            variation = random.uniform(0.2, 0.4)
        elif episode_num <= 3 or episode_num >= total_episodes - 2:
            variation = random.uniform(0.0, 0.2)
        else:
            variation = random.uniform(-0.2, 0.2)
        
        return round(min(10.0, max(1.0, base_rating + variation)), 1)
    
    def calculate_vocabulary_count(self, series_key: str, episode_num: int) -> int:
        """Calculate vocabulary count for episode"""
        min_vocab, max_vocab = self.anime_series[series_key]['vocabulary_range']
        return random.randint(min_vocab, max_vocab)
    
    def create_episode(self, series_key: str, episode_num: int) -> AnimeEpisode:
        """Create a single anime episode"""
        series = self.anime_series[series_key]
        
        # Standard languages for all anime
        languages = ["ja", "en"]  # Japanese original + English dub
        
        # Add additional languages for popular series
        if series_key in ["attack_on_titan", "death_note", "demon_slayer"]:
            languages.extend(["es", "fr", "de"])
        elif series_key in ["naruto", "one_piece"]:
            languages.extend(["es", "pt"])
        
        return AnimeEpisode(
            title=self.generate_episode_title(series_key, episode_num),
            description=self.generate_episode_description(series_key, episode_num),
            duration=24,  # Standard anime episode duration
            release_year=series['release_year'],
            difficulty_level=series['difficulty'],
            languages=languages,
            genres=series['genres'],
            thumbnail_url=f"{series['thumbnail_base']}?ep={episode_num}",
            video_url=f"{series['video_base']}/episode-{episode_num:02d}.mp4",
            is_premium=series['is_premium'],
            vocabulary_count=self.calculate_vocabulary_count(series_key, episode_num),
            imdb_rating=self.calculate_episode_rating(series_key, episode_num, series['total_episodes']),
            series_name=series['name'],
            episode_number=episode_num,
            season_number=series['season'],
            total_episodes_in_season=series['total_episodes']
        )
    
    def insert_episodes_batch(self, episodes: List[AnimeEpisode]) -> bool:
        """Insert a batch of episodes into the database"""
        try:
            # Prepare data for insertion
            episode_data = []
            for episode in episodes:
                data = {
                    "id": str(uuid.uuid4()),
                    "title": episode.title,
                    "description": episode.description,
                    "duration": episode.duration,
                    "release_year": episode.release_year,
                    "difficulty_level": episode.difficulty_level,
                    "languages": json.dumps(episode.languages),  # Convert to JSON
                    "genres": json.dumps(episode.genres),        # Convert to JSON
                    "thumbnail_url": episode.thumbnail_url,
                    "video_url": episode.video_url,
                    "is_premium": episode.is_premium,
                    "vocabulary_count": episode.vocabulary_count,
                    "imdb_rating": episode.imdb_rating,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                episode_data.append(data)
            
            # Use admin client to bypass RLS
            response = supabase_admin.table("movies").insert(episode_data).execute()
            
            if response.data:
                print(f"✅ Successfully inserted {len(response.data)} episodes")
                return True
            else:
                print(f"❌ Failed to insert episodes - no data returned")
                return False
                
        except Exception as e:
            print(f"❌ Database insertion error: {str(e)}")
            return False
    
    def populate_series(self, series_key: str, max_episodes: int = None) -> int:
        """Populate database with episodes from a single series"""
        series = self.anime_series[series_key]
        total_episodes = series['total_episodes']
        
        if max_episodes:
            total_episodes = min(total_episodes, max_episodes)
        
        print(f"\n📺 Processing {series['name']} ({total_episodes} episodes)")
        print(f"   Difficulty: {series['difficulty']} | Premium: {series['is_premium']}")
        
        episodes_added = 0
        batch_size = 10  # Process in batches to avoid overwhelming the database
        
        for start_ep in range(1, total_episodes + 1, batch_size):
            end_ep = min(start_ep + batch_size - 1, total_episodes)
            batch_episodes = []
            
            for episode_num in range(start_ep, end_ep + 1):
                episode = self.create_episode(series_key, episode_num)
                batch_episodes.append(episode)
            
            # Insert batch
            if self.insert_episodes_batch(batch_episodes):
                episodes_added += len(batch_episodes)
                print(f"   ✅ Episodes {start_ep}-{end_ep} added successfully")
            else:
                print(f"   ❌ Failed to add episodes {start_ep}-{end_ep}")
                break
        
        print(f"   📊 Total episodes added: {episodes_added}/{total_episodes}")
        return episodes_added
    
    def populate_priority_series(self) -> Dict[str, int]:
        """Populate Phase 1 priority series (smaller collections first)"""
        priority_series = [
            "my_hero_academia",    # 13 episodes
            "jujutsu_kaisen",      # 24 episodes  
            "attack_on_titan",     # 25 episodes
            "demon_slayer"         # 26 episodes
        ]
        
        results = {}
        total_added = 0
        
        print("🚀 Starting Phase 1: Priority Series Population")
        print("=" * 60)
        
        for series_key in priority_series:
            episodes_added = self.populate_series(series_key)
            results[series_key] = episodes_added
            total_added += episodes_added
        
        print(f"\n📊 Phase 1 Complete: {total_added} episodes added across {len(priority_series)} series")
        return results
    
    def populate_extended_series(self) -> Dict[str, int]:
        """Populate Phase 2 extended series (larger collections)"""
        extended_series = [
            "death_note",      # 37 episodes
            "dragon_ball_z",   # 39 episodes
            "one_piece",       # 61 episodes
            "naruto"           # 220 episodes
        ]
        
        results = {}
        total_added = 0
        
        print("\n🚀 Starting Phase 2: Extended Series Population")
        print("=" * 60)
        
        for series_key in extended_series:
            # For very long series like Naruto, we might want to limit initial population
            max_episodes = 50 if series_key == "naruto" else None
            episodes_added = self.populate_series(series_key, max_episodes)
            results[series_key] = episodes_added
            total_added += episodes_added
        
        print(f"\n📊 Phase 2 Complete: {total_added} episodes added across {len(extended_series)} series")
        return results
    
    def populate_all_series(self, phase: int = 1) -> Dict[str, Any]:
        """Main method to populate database with anime content"""
        start_time = datetime.now()
        print("🎌 CineFluent Anime Database Population Starting...")
        print(f"⏰ Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test database connection
        try:
            test_response = supabase.table("movies").select("id").limit(1).execute()
            print("✅ Database connection confirmed")
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            return {"error": "Database connection failed"}
        
        results = {
            "start_time": start_time.isoformat(),
            "phase": phase,
            "series_results": {},
            "total_episodes": 0,
            "success": False
        }
        
        try:
            if phase == 1:
                # Phase 1: Priority series (smaller, manageable collections)
                series_results = self.populate_priority_series()
            elif phase == 2:
                # Phase 2: Extended series (larger collections)
                series_results = self.populate_extended_series()
            else:
                # Full population (all series)
                series_results = {}
                series_results.update(self.populate_priority_series())
                series_results.update(self.populate_extended_series())
            
            results["series_results"] = series_results
            results["total_episodes"] = sum(series_results.values())
            results["success"] = True
            
        except Exception as e:
            print(f"❌ Population failed: {str(e)}")
            results["error"] = str(e)
        
        # Final summary
        end_time = datetime.now()
        duration = end_time - start_time
        
        results["end_time"] = end_time.isoformat()
        results["duration_seconds"] = duration.total_seconds()
        
        print("\n" + "=" * 60)
        print("🎌 POPULATION COMPLETE!")
        print("=" * 60)
        print(f"⏰ Duration: {duration}")
        print(f"📊 Total episodes added: {results['total_episodes']}")
        print(f"✅ Success: {results['success']}")
        
        if results["success"]:
            print("\n📈 Series Breakdown:")
            for series_key, count in results["series_results"].items():
                series_name = self.anime_series[series_key]["name"]
                print(f"   {series_name}: {count} episodes")
        
        return results
    
    def verify_population(self) -> Dict[str, Any]:
        """Verify the database population was successful"""
        print("\n🔍 Verifying database population...")
        
        try:
            # Get total count
            total_response = supabase.table("movies").select("id", count="exact").execute()
            total_count = total_response.count
            
            # Get counts by difficulty
            beginner_response = supabase.table("movies")\
                .select("id", count="exact")\
                .eq("difficulty_level", "beginner")\
                .execute()
            
            intermediate_response = supabase.table("movies")\
                .select("id", count="exact")\
                .eq("difficulty_level", "intermediate")\
                .execute()
            
            advanced_response = supabase.table("movies")\
                .select("id", count="exact")\
                .eq("difficulty_level", "advanced")\
                .execute()
            
            # Get premium vs free counts
            premium_response = supabase.table("movies")\
                .select("id", count="exact")\
                .eq("is_premium", True)\
                .execute()
            
            free_response = supabase.table("movies")\
                .select("id", count="exact")\
                .eq("is_premium", False)\
                .execute()
            
            # Sample data check
            sample_response = supabase.table("movies")\
                .select("title, series_name, difficulty_level, languages, genres")\
                .limit(5)\
                .execute()
            
            verification_results = {
                "total_episodes": total_count,
                "difficulty_breakdown": {
                    "beginner": beginner_response.count,
                    "intermediate": intermediate_response.count,
                    "advanced": advanced_response.count
                },
                "content_type": {
                    "premium": premium_response.count,
                    "free": free_response.count
                },
                "sample_data": sample_response.data[:3] if sample_response.data else []
            }
            
            print("✅ Verification complete!")
            print(f"📊 Total episodes in database: {total_count}")
            print(f"🎯 Difficulty distribution:")
            print(f"   - Beginner: {beginner_response.count}")
            print(f"   - Intermediate: {intermediate_response.count}")
            print(f"   - Advanced: {advanced_response.count}")
            print(f"💎 Content access:")
            print(f"   - Free: {free_response.count}")
            print(f"   - Premium: {premium_response.count}")
            
            return verification_results
            
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_existing_anime(self) -> bool:
        """Clean up existing anime entries (use with caution)"""
        print("⚠️  Cleaning up existing anime entries...")
        
        try:
            # Delete entries that look like anime (contain 'Episode' in title)
            response = supabase.table("movies")\
                .delete()\
                .ilike("title", "%Episode%")\
                .execute()
            
            print(f"🗑️  Cleaned up existing anime entries")
            return True
            
        except Exception as e:
            print(f"❌ Cleanup failed: {str(e)}")
            return False

def main():
    """Main execution function"""
    import sys
    
    populator = AnimeDBPopulator()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "clean":
            print("🗑️  Cleaning existing anime data...")
            populator.cleanup_existing_anime()
            
        elif command == "phase1":
            print("🚀 Running Phase 1: Priority Series")
            results = populator.populate_all_series(phase=1)
            
        elif command == "phase2":
            print("🚀 Running Phase 2: Extended Series")
            results = populator.populate_all_series(phase=2)
            
        elif command == "all":
            print("🚀 Running Full Population")
            results = populator.populate_all_series(phase=0)
            
        elif command == "verify":
            print("🔍 Verifying database content")
            populator.verify_population()
            
        else:
            print("❌ Unknown command. Use: clean, phase1, phase2, all, or verify")
            
    else:
        # Default: Run Phase 1 (priority series)
        print("🚀 Running default Phase 1 population...")
        results = populator.populate_all_series(phase=1)
        
        # Automatically verify after population
        if results.get("success"):
            print("\n" + "="*40)
            populator.verify_population()

if __name__ == "__main__":
    main()