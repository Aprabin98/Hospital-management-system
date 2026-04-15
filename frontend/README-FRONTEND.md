# Hospital Management System - Frontend (Next.js)

A modern, high-performance Next.js frontend for the Hospital Management System, featuring patient records management, appointment scheduling, and medical history tracking.

## Features

✅ **Performance Optimized**
- Server-Side Rendering (SSR) with Next.js 16
- Static Site Generation (SSG) where applicable
- Image optimization with Next.js Image component
- Automatic code splitting and lazy loading
- Fast build times with Turbopack

✅ **Authentication & Authorization**
- Token-based authentication (JWT)
- Role-based access control (Admin, Doctor, Patient, Staff)
- Secure token storage in localStorage
- Automatic token refresh on expired sessions

✅ **Core Features**
- Dashboard with statistics and quick actions
- Patient management (CRUD operations)
- Appointment scheduling
- Medical records management
- User settings and preferences

✅ **UI/UX**
- Tailwind CSS styling
- Responsive design (Mobile, Tablet, Desktop)
- Dark mode support (expandable)
- Toast notifications for user feedback
- Accessible components

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── dashboard/         # Dashboard page
│   ├── login/             # Login page
│   ├── patients/          # Patients list page
│   ├── appointments/      # Appointments page
│   ├── medical-records/   # Medical records page
│   ├── settings/          # Settings page
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Index page (redirects to login/dashboard)
├── components/            # Reusable React components
│   ├── Layout/            # Layout components (Header, Sidebar, MainLayout)
│   ├── Auth/              # Authentication components (LoginForm)
│   ├── Dashboard/         # Dashboard components
│   ├── MedicalRecords/    # Medical records components
│   ├── Appointments/      # Appointment components
│   ├── Common/            # Common reusable components
│   └── index.ts           # Component exports
├── hooks/                 # Custom React hooks
│   └── index.ts           # useApi, useAuth, useLocalStorage hooks
├── lib/                   # Utility libraries
│   └── api.ts             # Axios API client configuration
├── types/                 # TypeScript type definitions
│   └── index.ts           # Type definitions for API responses
└── globals.css            # Global Tailwind CSS styles

.env.local                 # Environment variables (local)
next.config.ts             # Next.js configuration
tsconfig.json              # TypeScript configuration
tailwind.config.ts         # Tailwind CSS configuration
postcss.config.mjs         # PostCSS configuration
package.json               # Project dependencies
```

## Environment Variables

Create a `.env.local` file in the root directory:

```env
# Backend API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# NextAuth Configuration (optional)
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key-here

# Application Settings
NEXT_PUBLIC_APP_NAME=Hospital Management System
NEXT_PUBLIC_APP_VERSION=1.0.0
```

## Installation & Setup

### Prerequisites
- Node.js 18+ and npm
- Backend Django API running on `http://localhost:8000`

### Steps

1. **Install dependencies**
   ```bash
   npm install
   ```

2. **Configure environment variables**
   - Copy `.env.local` and update with your backend API URL

3. **Start development server**
   ```bash
   npm run dev
   ```
   - Frontend will be available at `http://localhost:3000`

4. **Build for production**
   ```bash
   npm run build
   npm start
   ```

## API Integration

The frontend communicates with the Django backend via the `apiClient` configured in `src/lib/api.ts`:

### Example: Fetching data
```typescript
import { apiClient } from '@/lib/api';
import { Patient, PaginatedResponse } from '@/types';

const response = await apiClient.get<PaginatedResponse<Patient>>('/patients/');
const patients = response.results;
```

### Example: Posting data
```typescript
const newRecord = await apiClient.post('/medical-records/', {
  patient_id: '123',
  diagnosis: 'Flu',
  treatment: 'Rest and fluids',
});
```

## Custom Hooks

### useApi
Fetch data from the API and manage loading/error states:
```typescript
const { data, loading, error, refetch } = useApi<Patient[]>('/patients/');
```

### useAuth
Manage authentication and user role:
```typescript
const { isAuthenticated, userRole, login, logout } = useAuth();
```

### useLocalStorage
Persist data to browser localStorage:
```typescript
const [user, setUser] = useLocalStorage('user', null);
```

## Component Architecture

### Layout Components
- **MainLayout**: Wraps pages with header and sidebar
- **Header**: Top navigation bar with user menu
- **Sidebar**: Navigation menu with role-based access

### Page Components
- **Login**: Authentication form
- **Dashboard**: Overview with statistics
- **Patients**: Patient list with CRUD operations
- **Appointments**: Appointment management
- **MedicalRecords**: Medical history records
- **Settings**: User preferences

## Performance Optimizations

1. **Code Splitting**: Automatic with Next.js App Router
2. **Image Optimization**: Next.js Image component
3. **Static Rendering**: Pages prerendered as static content
4. **Caching**: HTTP caching headers configured
5. **Bundle Analysis**: Use `npm run analyze` (configure in build)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Authentication Flow

1. User logs in via `/login` page
2. Credentials sent to backend API (`/api/auth/login/`)
3. Backend returns JWT token and user info
4. Token stored in localStorage
5. Token added to all API requests via interceptor
6. Automatic redirect to `/login` on 401 Unauthorized

## User Roles & Access

- **Admin**: Full access to all features
- **Doctor**: Patient, appointment, and medical records access
- **Patient**: Own appointment and medical records access
- **Staff**: Support role with limited access

## Deployment

### Vercel (Recommended)
```bash
vercel deploy
```

### Docker
```bash
docker build -t hms-frontend .
docker run -p 3000:3000 hms-frontend
```

### Traditional Server
```bash
npm run build
npm start
```

## Development Tips

- Use TypeScript for type safety
- Follow the existing component structure
- Create reusable components in `src/components/Common`
- Test components locally before committing
- Use the custom hooks for API communication
- Keep performance in mind when adding new features

## Troubleshooting

### API Connection Issues
- Ensure backend is running on the correct URL
- Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
- Verify CORS is enabled on the backend

### Authentication Issues
- Clear browser localStorage and try again
- Check token expiration in browser DevTools
- Verify backend auth endpoint returns correct token

### Build Errors
- Run `npm install` to ensure all dependencies are installed
- Delete `.next` folder and rebuild: `npm run build`
- Check TypeScript errors: `npm run type-check`

## Available Scripts

```bash
# Development
npm run dev              # Start dev server

# Production
npm run build            # Build for production
npm start                # Start production server

# Code Quality
npm run lint             # Run ESLint
npm run type-check       # Check TypeScript
npm run format           # Format code with Prettier
```

## Technologies Used

- **Next.js 16**: React framework with SSR/SSG
- **React 19**: UI library
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client
- **React Hot Toast**: Toast notifications
- **next-auth**: Optional authentication (commented out for now)

## Contributing

1. Create a feature branch: `git checkout -b feature/my-feature`
2. Commit changes: `git commit -am 'Add feature'`
3. Push to branch: `git push origin feature/my-feature`
4. Submit pull request

## License

MIT License - See LICENSE file for details

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the main backend API documentation
3. Contact the development team

---

**Last Updated**: April 13, 2026
**Next.js Version**: 16.2.3 (Turbopack)
**Node Environment**: Production-ready
