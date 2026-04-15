# Frontend-Backend Integration Guide

## Overview

This document provides setup instructions for integrating the Next.js frontend with the Django backend API.

## Prerequisites

### Backend Requirements
- Django backend running on `http://localhost:8000`
- API endpoints configured according to the specifications below
- CORS headers enabled for frontend origin (`http://localhost:3000`)

### Frontend Requirements
- Node.js 18+
- npm or yarn
- `.env.local` configured with correct API URL

## Backend API Endpoints Required

### Authentication
- **POST** `/api/auth/login/`
  - Body: `{ email, password }`
  - Response: `{ token, refresh?, user, role }`

- **POST** `/api/auth/logout/`
  - Headers: `Authorization: Bearer <token>`

### Patients
- **GET** `/api/patients/`
  - Response: `{ count, next, previous, results: [...] }`

- **POST** `/api/patients/`
  - Body: Patient data

- **GET** `/api/patients/{id}/`
- **PUT** `/api/patients/{id}/`
- **DELETE** `/api/patients/{id}/`

### Appointments
- **GET** `/api/appointments/`
  - Response: `{ count, next, previous, results: [...] }`

- **POST** `/api/appointments/`

- **GET** `/api/appointments/{id}/`
- **PUT** `/api/appointments/{id}/`

### Medical Records
- **GET** `/api/medical-records/`
  - Response: `{ count, next, previous, results: [...] }`

- **POST** `/api/medical-records/`

- **GET** `/api/medical-records/{id}/`
- **PUT** `/api/medical-records/{id}/`

### Dashboard
- **GET** `/api/dashboard/stats`
  - Response: `{ total_patients, total_appointments, pending_appointments, total_doctors }`

## Setup Instructions

### 1. Backend Configuration

Ensure your Django backend includes these settings:

```python
# settings.py

INSTALLED_APPS = [
    # ... other apps
    'corsheaders',  # Add CORS middleware
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add early in middleware
    # ... other middleware
]

# Enable CORS for frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Optional: For production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
```

### 2. Frontend Configuration

1. **Update `.env.local`**:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

### 3. Testing the Integration

1. **Access the frontend**:
   - Navigate to `http://localhost:3000`
   - Should redirect to login page

2. **Test login flow**:
   - Enter credentials used in backend
   - Should redirect to dashboard on success
   - Check browser DevTools for token in localStorage

3. **Test data fetching**:
   - Navigate to Patients page
   - Should display list of patients from backend
   - Check Network tab in DevTools for API calls

## API Response Format

### Success Response
```json
{
  "status": "success",
  "data": {...}
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

### Paginated Response
```json
{
  "count": 100,
  "next": "/api/patients/?page=2",
  "previous": null,
  "results": [...]
}
```

## Authentication Token Management

### How It Works

1. **Login**: Frontend sends credentials to `POST /api/auth/login/`
2. **Token Storage**: Backend returns token, frontend stores in localStorage
3. **Request Headers**: API client automatically adds token to all requests:
   ```
   Authorization: Bearer <token>
   ```
4. **Token Expiration**: On 401 response, frontend clears token and redirects to login

### Refresh Token (Optional)

If backend supports token refresh:

```typescript
// In src/lib/api.ts, update response interceptor:
if (error.response?.status === 401) {
  const refreshToken = localStorage.getItem('refreshToken');
  if (refreshToken) {
    // Call refresh endpoint
    const newToken = await refreshTokens(refreshToken);
    // Update localStorage and retry request
  }
}
```

## Troubleshooting Integration Issues

### Issue: CORS Errors
**Error Message**: `Access to XMLHttpRequest blocked by CORS policy`

**Solution**:
1. Verify CORS configuration in Django settings
2. Check frontend API URL matches backend origin
3. Restart Django development server
4. Clear browser cache

### Issue: 401 Unauthorized
**Error Message**: `Token not found or invalid`

**Solution**:
1. Ensure login endpoint exists and returns token
2. Verify token format in localStorage
3. Check Authorization header in API requests (Network tab)
4. Verify backend JWT configuration

### Issue: 404 Not Found
**Error Message**: `Cannot GET /api/patients/`

**Solution**:
1. Verify API endpoint exists in backend
2. Check URL doesn't have typos
3. Verify API prefix is correct (check .env.local)
4. Restart backend server

### Issue: Slow API Responses
**Solution**:
1. Check backend server is running properly
2. Monitor backend logs for errors
3. Check network latency in DevTools
4. Consider adding caching if needed

## Performance Optimization Tips

### 1. Enable API Caching
```typescript
// Add cache headers to API responses
const response = await apiClient.get('/patients/', {
  headers: {
    'Cache-Control': 'max-age=300'  // 5 minutes
  }
});
```

### 2. Implement Pagination
```typescript
// Fetch paginated data
const response = await apiClient.get('/patients/?page=1&limit=10');
```

### 3. Lazy Load Data
```typescript
// Load data on demand
const { data, loading, error, refetch } = useApi('/patients/', { immediate: false });

// Trigger load on user action
const handleLoadPatients = () => refetch();
```

### 4. Optimize Bundle Size
```bash
# Analyze bundle
npm run build && npm run analyze
```

## Development Tools

### API Testing
- **Postman**: Test API endpoints directly
- **Thunder Client**: VS Code extension for API testing
- **curl**: Command-line API testing

### Browser DevTools
- **Network Tab**: Monitor API calls
- **Application Tab**: Check localStorage tokens
- **Console**: Debug errors

### Backend Debugging
```python
# Add logging to Django views
import logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
def login(request):
    logger.info(f"Login attempt: {request.data}")
    # ... login logic
```

## Deployment Checklist

- [ ] Backend API deployed with correct CORS configuration
- [ ] Frontend `.env.local` uses production API URL
- [ ] HTTPS configured on both frontend and backend
- [ ] SSL certificates valid and not expired
- [ ] Token expiration and refresh logic tested
- [ ] Error handling and user feedback in place
- [ ] Monitoring and logging configured
- [ ] Rate limiting implemented on backend
- [ ] Security headers configured
- [ ] Database backups automated

## Production Considerations

### Security
1. **HTTPS Only**: Require HTTPS on both frontend and backend
2. **Token Security**: Use httpOnly cookies instead of localStorage
3. **CORS**: Restrict to specific domains
4. **Rate Limiting**: Implement on backend API
5. **Input Validation**: Validate all user inputs

### Performance
1. **CDN**: Use CDN for frontend static assets
2. **Caching**: Implement appropriate cache strategies
3. **Compression**: Enable gzip compression
4. **Database**: Optimize queries and indexes

### Monitoring
1. **Error Tracking**: Use Sentry or similar service
2. **Performance Monitoring**: Monitor API response times
3. **Analytics**: Track user behavior
4. **Logging**: Centralized log management

## Common Integration Patterns

### Data Fetching with Error Handling
```typescript
'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

export default function Component() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get('/endpoint/');
        setData(response);
      } catch (err) {
        setError(err);
        toast.error('Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  return <div>{/* Render data */}</div>;
}
```

### Form Submission with API
```typescript
const handleSubmit = async (formData) => {
  try {
    const response = await apiClient.post('/endpoint/', formData);
    toast.success('Created successfully');
    router.push('/list');
  } catch (error) {
    toast.error(error.message);
  }
};
```

## Support & Resources

- **Next.js Docs**: https://nextjs.org/docs
- **React Docs**: https://react.dev
- **Django REST Framework Docs**: https://www.django-rest-framework.org
- **Axios Docs**: https://axios-http.com

---

**Last Updated**: April 13, 2026
**Version**: 1.0.0
