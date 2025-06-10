// CineFluent API - React Component Examples
// Copy these components into your React project

import React, { useState, useEffect } from 'react'

// ===========================================
// TYPES
// ===========================================

interface Movie {
  id: string
  title: string
  description: string
  duration: number
  release_year: number
  difficulty_level: string
  languages: string[]
  genres: string[]
  thumbnail_url: string
  is_premium: boolean
  vocabulary_count: number
  imdb_rating?: number
}

interface User {
  id: string
  email: string
  role: string
}

// ===========================================
// API SERVICE
// ===========================================

const API_BASE_URL = 'https://cinefluent-api-production.up.railway.app'

class CineFluentAPI {
  private token: string | null = null

  setToken(token: string) {
    this.token = token
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${API_BASE_URL}${endpoint}`
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
      headers.Authorization = `Bearer ${this.token}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Auth methods
  async login(email: string, password: string) {
    const result = await this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    this.setToken(result.access_token)
    return result
  }

  async register(email: string, password: string, full_name?: string) {
    const result = await this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    })
    this.setToken(result.access_token)
    return result
  }

  async getCurrentUser() {
    return this.request('/api/v1/auth/me')
  }

  // Movies methods
  async getMovies(page = 1, limit = 20, filters: any = {}) {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters,
    })
    return this.request(`/api/v1/movies?${params}`)
  }

  async getFeaturedMovies() {
    return this.request('/api/v1/movies/featured')
  }

  async searchMovies(query: string, limit = 10) {
    const params = new URLSearchParams({ q: query, limit: limit.toString() })
    return this.request(`/api/v1/movies/search?${params}`)
  }

  async getMovie(id: string) {
    return this.request(`/api/v1/movies/${id}`)
  }

  // Progress methods
  async updateProgress(movieId: string, progressPercentage: number, timeWatched: number) {
    return this.request('/api/v1/progress/update', {
      method: 'POST',
      body: JSON.stringify({
        movie_id: movieId,
        progress_percentage: progressPercentage,
        time_watched: timeWatched,
      }),
    })
  }

  async getProgressStats() {
    return this.request('/api/v1/progress/stats')
  }
}

// Global API instance
const api = new CineFluentAPI()

// ===========================================
// CUSTOM HOOKS
// ===========================================

// Auth Hook
export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const login = async (email: string, password: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.login(email, password)
      setUser(result.user)
      localStorage.setItem('cinefluent_token', result.access_token)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const register = async (email: string, password: string, fullName?: string) => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.register(email, password, fullName)
      setUser(result.user)
      localStorage.setItem('cinefluent_token', result.access_token)
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
      throw err
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('cinefluent_token')
    api.setToken('')
  }

  // Load token on mount
  useEffect(() => {
    const token = localStorage.getItem('cinefluent_token')
    if (token) {
      api.setToken(token)
      api.getCurrentUser()
        .then(userData => setUser(userData.user))
        .catch(() => {
          localStorage.removeItem('cinefluent_token')
        })
    }
  }, [])

  return { user, login, register, logout, loading, error }
}

// Movies Hook
export const useMovies = (filters: any = {}) => {
  const [movies, setMovies] = useState<Movie[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    page: 1,
    total: 0,
    per_page: 20,
  })

  const fetchMovies = async (page = 1) => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await api.getMovies(page, 20, filters)
      setMovies(result.movies)
      setPagination({
        page: result.page,
        total: result.total,
        per_page: result.per_page,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch movies')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMovies()
  }, [JSON.stringify(filters)])

  return { movies, loading, error, pagination, fetchMovies }
}

// ===========================================
// COMPONENTS
// ===========================================

// Login Form Component
export const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { login, loading, error } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(email, password)
      alert('Login successful!')
    } catch (error) {
      // Error is handled by the hook
    }
  }

  return (
    <form onSubmit={handleSubmit} className="login-form">
      <h2>Login to CineFluent</h2>
      
      {error && <div className="error">{error}</div>}
      
      <div className="form-group">
        <label htmlFor="email">Email:</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={loading}
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="password">Password:</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
      </div>
      
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  )
}

// Movie Card Component
export const MovieCard: React.FC<{ movie: Movie }> = ({ movie }) => {
  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return `${hours}h ${mins}m`
  }

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return '#4CAF50'
      case 'intermediate': return '#FF9800'
      case 'advanced': return '#F44336'
      default: return '#757575'
    }
  }

  return (
    <div className="movie-card">
      <div className="movie-poster">
        <img 
          src={movie.thumbnail_url} 
          alt={movie.title}
          onError={(e) => {
            e.currentTarget.src = '/placeholder-movie.jpg'
          }}
        />
        {movie.is_premium && <span className="premium-badge">Premium</span>}
      </div>
      
      <div className="movie-info">
        <h3 className="movie-title">{movie.title}</h3>
        <p className="movie-description">
          {movie.description.length > 100 
            ? `${movie.description.substring(0, 100)}...`
            : movie.description
          }
        </p>
        
        <div className="movie-metadata">
          <span className="duration">{formatDuration(movie.duration)}</span>
          <span className="year">{movie.release_year}</span>
          <span 
            className="difficulty"
            style={{ color: getDifficultyColor(movie.difficulty_level) }}
          >
            {movie.difficulty_level}
          </span>
        </div>
        
        <div className="movie-tags">
          {movie.languages.map(lang => (
            <span key={lang} className="language-tag">{lang.toUpperCase()}</span>
          ))}
          {movie.genres.map(genre => (
            <span key={genre} className="genre-tag">{genre}</span>
          ))}
        </div>
        
        <div className="movie-stats">
          <span className="rating">⭐ {movie.imdb_rating || 'N/A'}</span>
          <span className="vocabulary">📚 {movie.vocabulary_count} words</span>
        </div>
      </div>
    </div>
  )
}

// Movies List Component
export const MoviesList: React.FC = () => {
  const [filters, setFilters] = useState({})
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Movie[]>([])
  const [isSearching, setIsSearching] = useState(false)
  
  const { movies, loading, error, pagination, fetchMovies } = useMovies(filters)

  const handleSearch = async (query: string) => {
    setSearchQuery(query)
    
    if (!query.trim()) {
      setSearchResults([])
      setIsSearching(false)
      return
    }

    setIsSearching(true)
    try {
      const result = await api.searchMovies(query)
      setSearchResults(result.movies)
    } catch (err) {
      console.error('Search failed:', err)
      setSearchResults([])
    }
  }

  const displayMovies = searchQuery ? searchResults : movies

  if (loading) {
    return <div className="loading">Loading movies...</div>
  }

  if (error) {
    return <div className="error">Error: {error}</div>
  }

  return (
    <div className="movies-container">
      <div className="movies-header">
        <h1>CineFluent Movies</h1>
        
        <div className="search-bar">
          <input
            type="text"
            placeholder="Search movies..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filters">
          <select 
            onChange={(e) => setFilters({...filters, difficulty: e.target.value || undefined})}
            defaultValue=""
          >
            <option value="">All Difficulties</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
          
          <select 
            onChange={(e) => setFilters({...filters, language: e.target.value || undefined})}
            defaultValue=""
          >
            <option value="">All Languages</option>
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
          </select>
        </div>
      </div>
      
      <div className="movies-grid">
        {displayMovies.map(movie => (
          <MovieCard key={movie.id} movie={movie} />
        ))}
      </div>
      
      {!searchQuery && (
        <div className="pagination">
          <button 
            onClick={() => fetchMovies(pagination.page - 1)}
            disabled={pagination.page <= 1}
          >
            Previous
          </button>
          
          <span>
            Page {pagination.page} of {Math.ceil(pagination.total / pagination.per_page)}
          </span>
          
          <button 
            onClick={() => fetchMovies(pagination.page + 1)}
            disabled={pagination.page >= Math.ceil(pagination.total / pagination.per_page)}
          >
            Next
          </button>
        </div>
      )}
      
      {searchQuery && (
        <div className="search-info">
          Found {searchResults.length} movies matching "{searchQuery}"
        </div>
      )}
    </div>
  )
}

// Featured Movies Component
export const FeaturedMovies: React.FC = () => {
  const [featuredMovies, setFeaturedMovies] = useState<Movie[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchFeatured = async () => {
      try {
        const result = await api.getFeaturedMovies()
        setFeaturedMovies(result.movies)
      } catch (error) {
        console.error('Failed to fetch featured movies:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchFeatured()
  }, [])

  if (loading) {
    return <div className="loading">Loading featured movies...</div>
  }

  return (
    <section className="featured-section">
      <h2>Featured Movies</h2>
      <div className="featured-grid">
        {featuredMovies.map(movie => (
          <MovieCard key={movie.id} movie={movie} />
        ))}
      </div>
    </section>
  )
}

// User Profile Component
export const UserProfile: React.FC = () => {
  const { user, logout } = useAuth()
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      if (!user) return
      
      try {
        const result = await api.getProgressStats()
        setStats(result)
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [user])

  if (!user) {
    return <div>Please log in to view your profile.</div>
  }

  return (
    <div className="user-profile">
      <div className="profile-header">
        <h2>Welcome, {user.email}!</h2>
        <button onClick={logout} className="logout-btn">
          Logout
        </button>
      </div>
      
      {loading ? (
        <div className="loading">Loading stats...</div>
      ) : stats ? (
        <div className="stats-grid">
          <div className="stat-card">
            <h3>Movies Watched</h3>
            <p className="stat-number">{stats.total_movies_watched}</p>
          </div>
          
          <div className="stat-card">
            <h3>Completed</h3>
            <p className="stat-number">{stats.completed_movies}</p>
          </div>
          
          <div className="stat-card">
            <h3>Time Watched</h3>
            <p className="stat-number">
              {Math.round(stats.total_time_watched / 3600)}h
            </p>
          </div>
          
          <div className="stat-card">
            <h3>Words Learned</h3>
            <p className="stat-number">{stats.total_vocabulary_learned}</p>
          </div>
          
          <div className="stat-card">
            <h3>Average Progress</h3>
            <p className="stat-number">{stats.average_progress}%</p>
          </div>
        </div>
      ) : (
        <div>No learning stats available yet. Start watching movies!</div>
      )}
    </div>
  )
}

// API Health Component
export const ApiHealth: React.FC = () => {
  const [health, setHealth] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/health`)
        const data = await response.json()
        setHealth(data)
      } catch (error) {
        setHealth({ status: 'error', error: error.message })
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
    
    // Check health every 30 seconds
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <div className="loading">Checking API health...</div>
  }

  const isHealthy = health?.status === 'healthy'

  return (
    <div className={`health-status ${isHealthy ? 'healthy' : 'unhealthy'}`}>
      <h3>API Status</h3>
      <div className="status-indicator">
        <span className={`status-dot ${isHealthy ? 'green' : 'red'}`}></span>
        <span className="status-text">
          {isHealthy ? 'Operational' : 'Issues Detected'}
        </span>
      </div>
      
      {health?.checks && (
        <div className="health-details">
          <div>Database: {health.checks.database}</div>
          <div>Auth: {health.checks.auth}</div>
        </div>
      )}
      
      <div className="last-updated">
        Last checked: {new Date().toLocaleTimeString()}
      </div>
    </div>
  )
}

// Main App Component
export const CineFluentApp: React.FC = () => {
  const { user } = useAuth()
  const [currentPage, setCurrentPage] = useState<'home' | 'movies' | 'profile'>('home')

  return (
    <div className="cinefluent-app">
      <header className="app-header">
        <h1>🎬 CineFluent</h1>
        <nav>
          <button 
            onClick={() => setCurrentPage('home')}
            className={currentPage === 'home' ? 'active' : ''}
          >
            Home
          </button>
          <button 
            onClick={() => setCurrentPage('movies')}
            className={currentPage === 'movies' ? 'active' : ''}
          >
            Movies
          </button>
          {user && (
            <button 
              onClick={() => setCurrentPage('profile')}
              className={currentPage === 'profile' ? 'active' : ''}
            >
              Profile
            </button>
          )}
        </nav>
        <ApiHealth />
      </header>
      
      <main className="app-main">
        {currentPage === 'home' && (
          <div>
            {!user ? (
              <LoginForm />
            ) : (
              <FeaturedMovies />
            )}
          </div>
        )}
        
        {currentPage === 'movies' && <MoviesList />}
        {currentPage === 'profile' && <UserProfile />}
      </main>
      
      <footer className="app-footer">
        <p>
          Powered by <a href="https://cinefluent-api-production.up.railway.app/docs" target="_blank">
            CineFluent API
          </a>
        </p>
      </footer>
    </div>
  )
}

// ===========================================
// CSS STYLES (Add to your CSS file)
// ===========================================

/*
.cinefluent-app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 2px solid #eee;
  margin-bottom: 30px;
}

.app-header nav button {
  margin: 0 10px;
  padding: 8px 16px;
  border: none;
  background: #f5f5f5;
  border-radius: 4px;
  cursor: pointer;
}

.app-header nav button.active {
  background: #007bff;
  color: white;
}

.login-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 30px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.movies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.movie-card {
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  transition: transform 0.2s;
}

.movie-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.movie-poster {
  position: relative;
  height: 200px;
  overflow: hidden;
}

.movie-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.premium-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: gold;
  color: black;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.movie-info {
  padding: 15px;
}

.movie-title {
  margin: 0 0 10px 0;
  font-size: 18px;
  font-weight: bold;
}

.movie-description {
  color: #666;
  margin-bottom: 15px;
  line-height: 1.4;
}

.movie-metadata {
  display: flex;
  gap: 15px;
  margin-bottom: 10px;
  font-size: 14px;
}

.movie-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 10px;
}

.language-tag, .genre-tag {
  padding: 2px 8px;
  font-size: 12px;
  border-radius: 12px;
  background: #e3f2fd;
  color: #1976d2;
}

.genre-tag {
  background: #f3e5f5;
  color: #7b1fa2;
}

.movie-stats {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #666;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

.stat-card {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  text-align: center;
}

.stat-number {
  font-size: 2em;
  font-weight: bold;
  color: #007bff;
  margin: 10px 0;
}

.health-status {
  padding: 10px;
  border-radius: 4px;
  font-size: 14px;
}

.health-status.healthy {
  background: #e8f5e8;
  color: #2e7d32;
}

.health-status.unhealthy {
  background: #ffebee;
  color: #c62828;
}

.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

.status-dot.green {
  background: #4caf50;
}

.status-dot.red {
  background: #f44336;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error {
  color: #f44336;
  background: #ffebee;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin: 30px 0;
}

.pagination button {
  padding: 8px 16px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.search-bar {
  margin: 20px 0;
}

.search-input {
  width: 100%;
  max-width: 400px;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 16px;
}

.filters {
  display: flex;
  gap: 10px;
  margin: 20px 0;
}

.filters select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
*/
