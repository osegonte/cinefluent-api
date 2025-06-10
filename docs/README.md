# 📚 CineFluent API Documentation

Complete documentation for integrating with the CineFluent API.

## 📋 Documentation Files

### 🔧 Core Documentation
- **[API_REFERENCE.md](./API_REFERENCE.md)** - Complete API endpoint reference
- **[FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)** - Frontend integration guide

### 📝 Examples & Code
- **[api-examples.js](./examples/api-examples.js)** - JavaScript/Node.js examples
- **[react-components.tsx](./examples/react-components.tsx)** - React component examples

### 🧪 Testing
- **[CineFluent_API.postman_collection.json](./postman/CineFluent_API.postman_collection.json)** - Postman collection

## 🚀 Quick Start

### 1. Test the API
```bash
# Import Postman collection
# Or visit: https://cinefluent-api-production.up.railway.app/docs
```

### 2. Frontend Integration
```typescript
const API_BASE_URL = 'https://cinefluent-api-production.up.railway.app'

// Test connection
fetch(`${API_BASE_URL}/api/v1/health`)
  .then(res => res.json())
  .then(data => console.log('API Status:', data))
```

### 3. Authentication Flow
```typescript
// 1. Register/Login
const auth = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
})

// 2. Use token for authenticated requests
const movies = await fetch(`${API_BASE_URL}/api/v1/movies`, {
  headers: { 'Authorization': `Bearer ${token}` }
})
```

## 🎯 Key Features

### ✅ **Authentication System**
- JWT-based authentication via Supabase
- User registration and login
- Token refresh mechanism
- Profile management

### ✅ **Movies Catalog**
- Paginated movie listings
- Search functionality
- Category and language filtering
- Featured movies

### ✅ **Learning Progress**
- Track viewing progress
- Vocabulary learning stats
- User analytics dashboard

### ✅ **Subtitle Processing**
- Upload SRT/VTT files
- NLP-powered vocabulary extraction
- Interactive learning segments

## 📊 API Status

- **Live URL**: https://cinefluent-api-production.up.railway.app
- **Health Check**: https://cinefluent-api-production.up.railway.app/api/v1/health
- **Interactive Docs**: https://cinefluent-api-production.up.railway.app/docs
- **OpenAPI JSON**: https://cinefluent-api-production.up.railway.app/openapi.json

## 🛠️ Environment Setup

### Production
```env
VITE_API_BASE_URL=https://cinefluent-api-production.up.railway.app
VITE_API_VERSION=v1
VITE_ENVIRONMENT=production
```

### Development
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_VERSION=v1
VITE_ENVIRONMENT=development
```

## 🔗 Additional Resources

- **Repository**: [GitHub Repository]
- **Support**: Create issues in the repository
- **Live Demo**: Try the interactive documentation

---

**🎬 CineFluent API - Ready for Frontend Integration! 🚀**
