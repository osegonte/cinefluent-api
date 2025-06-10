// CineFluent API - JavaScript Examples
// Copy and paste these examples into your browser console or Node.js

const API_BASE_URL = 'https://cinefluent-api-production.up.railway.app'

// ===========================================
// AUTHENTICATION EXAMPLES
// ===========================================

// 1. Register a new user
async function registerUser() {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: 'demo@cinefluent.com',
      password: 'demopassword123',
      full_name: 'Demo User'
    })
  })
  
  const data = await response.json()
  console.log('Register Response:', data)
  return data
}

// 2. Login user
async function loginUser() {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: 'demo@cinefluent.com',
      password: 'demopassword123'
    })
  })
  
  const data = await response.json()
  console.log('Login Response:', data)
  
  // Store token for future requests
  window.CINEFLUENT_TOKEN = data.access_token
  return data
}

// 3. Get current user
async function getCurrentUser() {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
    headers: {
      'Authorization': `Bearer ${window.CINEFLUENT_TOKEN}`
    }
  })
  
  const data = await response.json()
  console.log('Current User:', data)
  return data
}

// ===========================================
// MOVIES EXAMPLES
// ===========================================

// 4. Get movies with pagination
async function getMovies(page = 1, limit = 20) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/movies?page=${page}&limit=${limit}`
  )
  
  const data = await response.json()
  console.log('Movies:', data)
  return data
}

// 5. Get featured movies
async function getFeaturedMovies() {
  const response = await fetch(`${API_BASE_URL}/api/v1/movies/featured`)
  const data = await response.json()
  console.log('Featured Movies:', data)
  return data
}

// 6. Search movies
async function searchMovies(query) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/movies/search?q=${encodeURIComponent(query)}`
  )
  
  const data = await response.json()
  console.log('Search Results:', data)
  return data
}

// 7. Get movie categories
async function getCategories() {
  const response = await fetch(`${API_BASE_URL}/api/v1/categories`)
  const data = await response.json()
  console.log('Categories:', data)
  return data
}

// 8. Get available languages
async function getLanguages() {
  const response = await fetch(`${API_BASE_URL}/api/v1/languages`)
  const data = await response.json()
  console.log('Languages:', data)
  return data
}

// ===========================================
// PROGRESS EXAMPLES (Requires Authentication)
// ===========================================

// 9. Update learning progress
async function updateProgress(movieId, progressPercentage, timeWatched) {
  const response = await fetch(`${API_BASE_URL}/api/v1/progress/update`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${window.CINEFLUENT_TOKEN}`
    },
    body: JSON.stringify({
      movie_id: movieId,
      progress_percentage: progressPercentage,
      time_watched: timeWatched,
      vocabulary_learned: 5
    })
  })
  
  const data = await response.json()
  console.log('Progress Updated:', data)
  return data
}

// 10. Get progress statistics
async function getProgressStats() {
  const response = await fetch(`${API_BASE_URL}/api/v1/progress/stats`, {
    headers: {
      'Authorization': `Bearer ${window.CINEFLUENT_TOKEN}`
    }
  })
  
  const data = await response.json()
  console.log('Progress Stats:', data)
  return data
}

// ===========================================
// UTILITY EXAMPLES
// ===========================================

// 11. Check API health
async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`)
  const data = await response.json()
  console.log('API Health:', data)
  return data
}

// 12. Get API root info
async function getApiInfo() {
  const response = await fetch(`${API_BASE_URL}/`)
  const data = await response.json()
  console.log('API Info:', data)
  return data
}

// ===========================================
// DEMO WORKFLOW
// ===========================================

// Run complete demo workflow
async function runDemo() {
  console.log('🎬 CineFluent API Demo Starting...')
  
  try {
    // 1. Check API health
    console.log('\n1. Checking API health...')
    await checkHealth()
    
    // 2. Get featured movies (public)
    console.log('\n2. Getting featured movies...')
    await getFeaturedMovies()
    
    // 3. Search movies (public)
    console.log('\n3. Searching for movies...')
    await searchMovies('action')
    
    // 4. Get categories
    console.log('\n4. Getting categories...')
    await getCategories()
    
    // 5. Get languages
    console.log('\n5. Getting languages...')
    await getLanguages()
    
    console.log('\n✅ Demo completed successfully!')
    console.log('\n🔐 To test authenticated features:')
    console.log('   - Run registerUser() or loginUser()')
    console.log('   - Then run getCurrentUser(), getProgressStats(), etc.')
    
  } catch (error) {
    console.error('❌ Demo failed:', error)
  }
}

// ===========================================
// ADVANCED EXAMPLES
// ===========================================

// Error handling wrapper
async function apiCall(fn, ...args) {
  try {
    return await fn(...args)
  } catch (error) {
    console.error('API Error:', error)
    throw error
  }
}

// Retry with exponential backoff
async function retryApiCall(fn, maxRetries = 3, delay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      if (i === maxRetries - 1) throw error
      
      console.log(`Retry ${i + 1}/${maxRetries} after ${delay}ms...`)
      await new Promise(resolve => setTimeout(resolve, delay))
      delay *= 2 // Exponential backoff
    }
  }
}

// Batch API calls
async function batchApiCalls(calls) {
  const results = await Promise.allSettled(calls)
  
  results.forEach((result, index) => {
    if (result.status === 'fulfilled') {
      console.log(`Call ${index + 1} succeeded:`, result.value)
    } else {
      console.error(`Call ${index + 1} failed:`, result.reason)
    }
  })
  
  return results
}

// ===========================================
// HOW TO USE
// ===========================================

console.log(`
🎬 CineFluent API Examples Loaded!

Quick Start:
1. runDemo()                    - Run complete demo
2. checkHealth()               - Check API status  
3. getFeaturedMovies()         - Get featured movies
4. searchMovies('action')      - Search for movies

Authentication Flow:
1. registerUser()              - Create account
2. loginUser()                 - Login (sets token)
3. getCurrentUser()            - Get user info
4. getProgressStats()          - Get learning stats

All functions are ready to use! 🚀
`)

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    registerUser,
    loginUser,
    getCurrentUser,
    getMovies,
    getFeaturedMovies,
    searchMovies,
    updateProgress,
    checkHealth,
    runDemo
  }
}
