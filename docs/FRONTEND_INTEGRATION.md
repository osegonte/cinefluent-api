# 🚀 CineFluent Frontend Integration Guide

## 🎯 Quick Start

### Environment Setup
Add these to your frontend `.env.local`:

```env
VITE_API_BASE_URL=https://cinefluent-api-production.up.railway.app
VITE_API_VERSION=v1
VITE_ENVIRONMENT=production
```

### Base Configuration

```typescript
// api/config.ts
export const API_CONFIG = {
  BASE_URL: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
  VERSION: process.env.VITE_API_VERSION || 'v1',
  TIMEOUT: 10000,
}

export const API_ENDPOINTS = {
  // Auth
  REGISTER: '/api/v1/auth/register',
  LOGIN: '/api/v1/auth/login',
  ME: '/api/v1/auth/me',
  REFRESH: '/api/v1/auth/refresh',
  LOGOUT: '/api/v1/auth/logout',
  
  // Movies
  MOVIES: '/api/v1/movies',
  MOVIES_FEATURED: '/api/v1/movies/featured',
  MOVIES_SEARCH: '/api/v1/movies/search',
  CATEGORIES: '/api/v1/categories',
  LANGUAGES: '/api/v1/languages',
  
  // Progress
  PROGRESS_UPDATE: '/api/v1/progress/update',
  PROGRESS_STATS: '/api/v1/progress/stats',
  
  // Subtitles
  SUBTITLES_UPLOAD: '/api/v1/subtitles/upload',
}
```

## 🔐 Authentication Implementation

### Auth Service
```typescript
// services/auth.service.ts
import { API_CONFIG, API_ENDPOINTS } from '../config'

interface User {
  id: string
  email: string
  role: string
}

interface LoginData {
  email: string
  password: string
}

interface RegisterData extends LoginData {
  full_name?: string
}

interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

class AuthService {
  private baseUrl = API_CONFIG.BASE_URL
  
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.REGISTER}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }
    
    return response.json()
  }
  
  async login(data: LoginData): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.LOGIN}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }
    
    return response.json()
  }
  
  async getCurrentUser(token: string): Promise<User> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.ME}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
    
    if (!response.ok) {
      throw new Error('Failed to get user')
    }
    
    const data = await response.json()
    return data.user
  }
  
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.REFRESH}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    
    if (!response.ok) {
      throw new Error('Token refresh failed')
    }
    
    return response.json()
  }
  
  async logout(token: string): Promise<void> {
    await fetch(`${this.baseUrl}${API_ENDPOINTS.LOGOUT}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    })
  }
}

export const authService = new AuthService()
```

### Token Management
```typescript
// utils/token.ts
const TOKEN_KEY = 'cinefluent_token'
const REFRESH_TOKEN_KEY = 'cinefluent_refresh_token'

export const tokenManager = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },
  
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },
  
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  
  setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  },
  
  clearTokens(): void {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
  
  isTokenExpired(token: string): boolean {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      return payload.exp * 1000 < Date.now()
    } catch {
      return true
    }
  }
}
```

## 🎬 Movies Service

```typescript
// services/movies.service.ts
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

interface MoviesResponse {
  movies: Movie[]
  total: number
  page: number
  per_page: number
}

interface MoviesFilters {
  page?: number
  limit?: number
  language?: string
  difficulty?: string
  genre?: string
}

class MoviesService {
  private baseUrl = API_CONFIG.BASE_URL
  
  async getMovies(filters: MoviesFilters = {}): Promise<MoviesResponse> {
    const params = new URLSearchParams()
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) {
        params.append(key, value.toString())
      }
    })
    
    const response = await fetch(
      `${this.baseUrl}${API_ENDPOINTS.MOVIES}?${params}`
    )
    
    if (!response.ok) {
      throw new Error('Failed to fetch movies')
    }
    
    return response.json()
  }
  
  async getFeaturedMovies(): Promise<{ movies: Movie[] }> {
    const response = await fetch(
      `${this.baseUrl}${API_ENDPOINTS.MOVIES_FEATURED}`
    )
    
    if (!response.ok) {
      throw new Error('Failed to fetch featured movies')
    }
    
    return response.json()
  }
  
  async searchMovies(query: string, limit = 10): Promise<{
    movies: Movie[]
    query: string
    total: number
  }> {
    const params = new URLSearchParams({ q: query, limit: limit.toString() })
    
    const response = await fetch(
      `${this.baseUrl}${API_ENDPOINTS.MOVIES_SEARCH}?${params}`
    )
    
    if (!response.ok) {
      throw new Error('Search failed')
    }
    
    return response.json()
  }
  
  async getMovie(id: string, token?: string): Promise<{
    movie: Movie
    user_progress?: any
  }> {
    const headers: Record<string, string> = {}
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    const response = await fetch(
      `${this.baseUrl}/api/v1/movies/${id}`,
      { headers }
    )
    
    if (!response.ok) {
      throw new Error('Failed to fetch movie')
    }
    
    return response.json()
  }
}

export const moviesService = new MoviesService()
```

## 📊 Progress Tracking

```typescript
// services/progress.service.ts
interface ProgressUpdate {
  movie_id: string
  progress_percentage: number
  time_watched: number
  vocabulary_learned?: number
}

class ProgressService {
  private baseUrl = API_CONFIG.BASE_URL
  
  async updateProgress(data: ProgressUpdate, token: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}${API_ENDPOINTS.PROGRESS_UPDATE}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      }
    )
    
    if (!response.ok) {
      throw new Error('Failed to update progress')
    }
    
    return response.json()
  }
  
  async getStats(token: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}${API_ENDPOINTS.PROGRESS_STATS}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    )
    
    if (!response.ok) {
      throw new Error('Failed to fetch progress stats')
    }
    
    return response.json()
  }
}

export const progressService = new ProgressService()
```

## 🎯 React Hooks

### useAuth Hook
```typescript
// hooks/useAuth.ts
import { useState, useEffect, useContext, createContext } from 'react'
import { authService } from '../services/auth.service'
import { tokenManager } from '../utils/token'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  
  useEffect(() => {
    const initAuth = async () => {
      const savedToken = tokenManager.getToken()
      
      if (savedToken && !tokenManager.isTokenExpired(savedToken)) {
        try {
          const userData = await authService.getCurrentUser(savedToken)
          setUser(userData)
          setToken(savedToken)
        } catch (error) {
          tokenManager.clearTokens()
        }
      }
      
      setIsLoading(false)
    }
    
    initAuth()
  }, [])
  
  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password })
    
    setUser(response.user)
    setToken(response.access_token)
    
    tokenManager.setToken(response.access_token)
    tokenManager.setRefreshToken(response.refresh_token)
  }
  
  const register = async (data: RegisterData) => {
    const response = await authService.register(data)
    
    setUser(response.user)
    setToken(response.access_token)
    
    tokenManager.setToken(response.access_token)
    tokenManager.setRefreshToken(response.refresh_token)
  }
  
  const logout = () => {
    if (token) {
      authService.logout(token)
    }
    
    setUser(null)
    setToken(null)
    tokenManager.clearTokens()
  }
  
  return (
    <AuthContext.Provider
      value={{ user, token, login, register, logout, isLoading }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
```

### useMovies Hook
```typescript
// hooks/useMovies.ts
import { useState, useEffect } from 'react'
import { moviesService } from '../services/movies.service'

export const useMovies = (filters: MoviesFilters = {}) => {
  const [movies, setMovies] = useState<Movie[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    per_page: 20,
  })
  
  useEffect(() => {
    const fetchMovies = async () => {
      try {
        setLoading(true)
        const response = await moviesService.getMovies(filters)
        
        setMovies(response.movies)
        setPagination({
          total: response.total,
          page: response.page,
          per_page: response.per_page,
        })
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch movies')
      } finally {
        setLoading(false)
      }
    }
    
    fetchMovies()
  }, [JSON.stringify(filters)])
  
  return { movies, loading, error, pagination }
}
```

## 🔄 Error Handling

```typescript
// utils/api.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export const handleApiError = (error: any) => {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 401:
        // Redirect to login
        window.location.href = '/login'
        break
      case 403:
        // Show upgrade to premium message
        console.error('Premium subscription required')
        break
      case 422:
        // Handle validation errors
        return error.data?.detail || 'Validation error'
      default:
        return error.message
    }
  }
  
  return 'An unexpected error occurred'
}
```

## 🎯 Example Usage

### Login Component
```typescript
// components/LoginForm.tsx
import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'

export const LoginForm = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    
    try {
      await login(email, password)
      // Redirect or update UI
    } catch (error) {
      console.error('Login failed:', error)
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
        required
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  )
}
```

### Movies List Component
```typescript
// components/MoviesList.tsx
import { useMovies } from '../hooks/useMovies'

export const MoviesList = () => {
  const { movies, loading, error, pagination } = useMovies({
    page: 1,
    limit: 20,
  })
  
  if (loading) return <div>Loading movies...</div>
  if (error) return <div>Error: {error}</div>
  
  return (
    <div>
      <div className="movies-grid">
        {movies.map((movie) => (
          <div key={movie.id} className="movie-card">
            <img src={movie.thumbnail_url} alt={movie.title} />
            <h3>{movie.title}</h3>
            <p>{movie.description}</p>
            <div className="metadata">
              <span>Duration: {movie.duration}min</span>
              <span>Difficulty: {movie.difficulty_level}</span>
              <span>Rating: {movie.imdb_rating}</span>
            </div>
          </div>
        ))}
      </div>
      
      <div className="pagination">
        <span>
          Showing {movies.length} of {pagination.total} movies
        </span>
      </div>
    </div>
  )
}
```

## 🎯 Testing

```typescript
// __tests__/auth.service.test.ts
import { authService } from '../services/auth.service'

// Mock fetch
global.fetch = jest.fn()

describe('AuthService', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('should login successfully', async () => {
    const mockResponse = {
      user: { id: '1', email: 'test@example.com' },
      access_token: 'token123',
      refresh_token: 'refresh123',
    }
    
    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })
    
    const result = await authService.login({
      email: 'test@example.com',
      password: 'password123',
    })
    
    expect(result).toEqual(mockResponse)
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/auth/login'),
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
      })
    )
  })
})
```

## 📱 Mobile Considerations

### React Native Setup
```typescript
// For React Native, replace localStorage with AsyncStorage
import AsyncStorage from '@react-native-async-storage/async-storage'

export const tokenManager = {
  async getToken(): Promise<string | null> {
    return await AsyncStorage.getItem(TOKEN_KEY)
  },
  
  async setToken(token: string): Promise<void> {
    await AsyncStorage.setItem(TOKEN_KEY, token)
  },
  
  async clearTokens(): Promise<void> {
    await AsyncStorage.multiRemove([TOKEN_KEY, REFRESH_TOKEN_KEY])
  },
}
```

## 🔄 Auto Token Refresh

```typescript
// utils/apiClient.ts
class ApiClient {
  private async makeRequest(
    url: string, 
    options: RequestInit = {}
  ): Promise<Response> {
    let token = tokenManager.getToken()
    
    // Check if token needs refresh
    if (token && tokenManager.isTokenExpired(token)) {
      const refreshToken = tokenManager.getRefreshToken()
      
      if (refreshToken) {
        try {
          const newAuth = await authService.refreshToken(refreshToken)
          token = newAuth.access_token
          
          tokenManager.setToken(newAuth.access_token)
          tokenManager.setRefreshToken(newAuth.refresh_token)
        } catch (error) {
          // Refresh failed, redirect to login
          tokenManager.clearTokens()
          window.location.href = '/login'
          throw new Error('Session expired')
        }
      }
    }
    
    // Add auth header if token exists
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }
    
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
    
    return fetch(url, {
      ...options,
      headers,
    })
  }
  
  async get(endpoint: string): Promise<any> {
    const response = await this.makeRequest(
      `${API_CONFIG.BASE_URL}${endpoint}`
    )
    
    if (!response.ok) {
      throw new ApiError(
        'Request failed',
        response.status,
        await response.json()
      )
    }
    
    return response.json()
  }
  
  async post(endpoint: string, data: any): Promise<any> {
    const response = await this.makeRequest(
      `${API_CONFIG.BASE_URL}${endpoint}`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    )
    
    if (!response.ok) {
      throw new ApiError(
        'Request failed',
        response.status,
        await response.json()
      )
    }
    
    return response.json()
  }
}

export const apiClient = new ApiClient()
```

## 🎯 Best Practices

### 1. Environment Variables
Always use environment variables for API URLs:
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
                    process.env.VITE_API_BASE_URL || 
                    'http://localhost:8000'
```

### 2. Type Safety
Define comprehensive TypeScript interfaces:
```typescript
// types/api.ts
export interface ApiResponse<T> {
  data?: T
  message?: string
  detail?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}
```

### 3. Loading States
Always handle loading states:
```typescript
const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)

// In your API calls
try {
  setLoading(true)
  setError(null)
  const result = await apiCall()
  // Handle success
} catch (err) {
  setError(err.message)
} finally {
  setLoading(false)
}
```

### 4. Error Boundaries
Implement error boundaries for API errors:
```typescript
class ApiErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />
    }
    
    return this.props.children
  }
}
```

## 🚀 Deployment Checklist

- [ ] Set correct API_BASE_URL in production
- [ ] Configure CORS for your frontend domain
- [ ] Test authentication flow end-to-end
- [ ] Verify file upload functionality
- [ ] Test error handling scenarios
- [ ] Implement proper loading states
- [ ] Add offline support (if needed)
- [ ] Set up error reporting (Sentry, etc.)

## 📞 Support

- **API Documentation**: https://cinefluent-api-production.up.railway.app/docs
- **Health Check**: https://cinefluent-api-production.up.railway.app/api/v1/health
- **Issues**: Create issues in the project repository

---

**Happy coding! Your CineFluent frontend integration should be smooth! 🎬✨**
