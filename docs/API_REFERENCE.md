# 🎬 CineFluent API Reference

**Version**: 1.0.0  
**Base URL**: https://cinefluent-api-production.up.railway.app  
**Documentation**: https://cinefluent-api-production.up.railway.app/docs  

## 📋 Table of Contents

- [Authentication](#authentication)
- [Movies API](#movies-api)
- [User Progress](#user-progress)
- [Subtitles & Learning](#subtitles--learning)
- [Error Handling](#error-handling)
- [Rate Limits](#rate-limits)

## 🔐 Authentication

### Overview
CineFluent uses JWT (JSON Web Tokens) for authentication via Supabase Auth.

### Base Headers
```http
Content-Type: application/json
Authorization: Bearer <your_jwt_token>
```

### Auth Endpoints

#### Register User
```http
POST /api/v1/auth/register
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "email_confirmed_at": "2025-06-10T12:00:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "User created successfully"
}
```

#### Login User
```http
POST /api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "expires_in": 3600,
  "message": "Login successful"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "authenticated"
  },
  "profile": {
    "id": "uuid",
    "username": "johndoe",
    "full_name": "John Doe",
    "native_language": "en",
    "learning_languages": ["es", "fr"],
    "learning_goals": {}
  }
}
```

#### Update Profile
```http
PUT /api/v1/auth/profile
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "username": "newusername",
  "full_name": "John Smith",
  "native_language": "en",
  "learning_languages": ["es", "fr", "de"],
  "learning_goals": {
    "daily_minutes": 30,
    "weekly_goals": 5
  }
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
```

**Request Body:**
```json
{
  "refresh_token": "your_refresh_token"
}
```

#### Logout
```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

## 🎬 Movies API

### Get Movies (Paginated)
```http
GET /api/v1/movies?page=1&limit=20&language=en&difficulty=beginner&genre=comedy
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (1-100, default: 20)
- `language` (string): Filter by language code
- `difficulty` (string): beginner | intermediate | advanced
- `genre` (string): Filter by genre

**Response (200):**
```json
{
  "movies": [
    {
      "id": "uuid",
      "title": "The Shawshank Redemption",
      "description": "Two imprisoned men bond over...",
      "duration": 142,
      "release_year": 1994,
      "difficulty_level": "intermediate",
      "languages": ["en"],
      "genres": ["drama"],
      "thumbnail_url": "https://example.com/poster.jpg",
      "video_url": "https://example.com/video.mp4",
      "is_premium": false,
      "vocabulary_count": 850,
      "imdb_rating": 9.3
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20
}
```

### Get Featured Movies
```http
GET /api/v1/movies/featured
```

**Response (200):**
```json
{
  "movies": [
    // Array of top-rated movies (max 6)
  ]
}
```

### Search Movies
```http
GET /api/v1/movies/search?q=shawshank
```

**Query Parameters:**
- `q` (string, required): Search query
- `limit` (int): Max results (1-50, default: 10)

**Response (200):**
```json
{
  "movies": [
    // Array of matching movies
  ],
  "query": "shawshank",
  "total": 1
}
```

### Get Movie Details
```http
GET /api/v1/movies/{movie_id}
```

**Response (200):**
```json
{
  "movie": {
    // Full movie object
  },
  "user_progress": {
    "progress_percentage": 45,
    "time_watched": 3840,
    "vocabulary_learned": 23,
    "last_watched_at": "2025-06-10T15:30:00Z"
  }
}
```

### Get Categories
```http
GET /api/v1/categories
```

**Response (200):**
```json
{
  "categories": [
    {
      "id": "action",
      "name": "Action",
      "description": "High-energy movies...",
      "sort_order": 1
    }
  ]
}
```

### Get Languages
```http
GET /api/v1/languages
```

**Response (200):**
```json
{
  "languages": ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
}
```

## 📊 User Progress

### Update Progress
```http
POST /api/v1/progress/update
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "movie_id": "uuid",
  "progress_percentage": 75,
  "time_watched": 5400,
  "vocabulary_learned": 15
}
```

**Response (200):**
```json
{
  "message": "Progress updated successfully",
  "progress": {
    "user_id": "uuid",
    "movie_id": "uuid",
    "progress_percentage": 75,
    "time_watched": 5400,
    "vocabulary_learned": 15,
    "last_watched_at": "2025-06-10T16:00:00Z"
  }
}
```

### Get Progress Stats
```http
GET /api/v1/progress/stats
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "total_movies_watched": 5,
  "completed_movies": 2,
  "total_time_watched": 18000,
  "total_vocabulary_learned": 127,
  "average_progress": 68.5,
  "recent_activity": [
    // Recent progress entries
  ]
}
```

## 📝 Subtitles & Learning

### Upload Subtitle File
```http
POST /api/v1/subtitles/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**
- `file`: Subtitle file (.srt or .vtt)
- `movie_id`: UUID of the movie
- `language`: Language code (e.g., "en")
- `title`: Optional subtitle title

**Response (200):**
```json
{
  "message": "Subtitle uploaded and processed successfully",
  "subtitle_id": "uuid",
  "stats": {
    "total_cues": 1250,
    "total_segments": 125,
    "duration": 7200.0,
    "vocabulary_count": 340,
    "avg_difficulty": 2.3
  }
}
```

### Get Movie Subtitles
```http
GET /api/v1/subtitles/movie/{movie_id}?language=en
```

**Response (200):**
```json
{
  "subtitles": [
    {
      "id": "uuid",
      "movie_id": "uuid",
      "language": "en",
      "title": "English Subtitles",
      "file_type": "srt",
      "total_cues": 1250,
      "total_segments": 125,
      "duration": 7200.0,
      "vocabulary_count": 340,
      "created_at": "2025-06-10T12:00:00Z"
    }
  ],
  "total": 1
}
```

### Get Learning Segments
```http
GET /api/v1/subtitles/{subtitle_id}/segments
```

**Response (200):**
```json
{
  "subtitle": {
    // Subtitle metadata
  },
  "segments": [
    {
      "id": "uuid",
      "start_time": 0.0,
      "end_time": 30.0,
      "difficulty_score": 2.1,
      "vocabulary_words": [
        {
          "word": "adventure",
          "difficulty_level": "intermediate",
          "definition": "An exciting experience"
        }
      ],
      "cue_count": 3,
      "user_progress": {
        "completed": false,
        "time_spent": 45,
        "words_learned": ["adventure"]
      }
    }
  ],
  "total_segments": 125
}
```

## ❌ Error Handling

### Standard Error Response
```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized  
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict (duplicate)
- `422` - Validation Error
- `500` - Internal Server Error

### Validation Errors (422)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## ⚡ Rate Limits

- **General API**: 1000 requests/hour per user
- **Authentication**: 100 requests/hour per IP
- **File Upload**: 10 uploads/hour per user

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1623456789
```

## 🔗 Additional Resources

- **Interactive Docs**: https://cinefluent-api-production.up.railway.app/docs
- **Health Check**: https://cinefluent-api-production.up.railway.app/api/v1/health
- **OpenAPI JSON**: https://cinefluent-api-production.up.railway.app/openapi.json
