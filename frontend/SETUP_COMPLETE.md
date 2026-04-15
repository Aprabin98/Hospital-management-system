# Hospital Management System - Frontend

A high-performance Next.js frontend for the Hospital Management System.

## 📚 Documentation

### Getting Started
- **[Frontend README](README-FRONTEND.md)** - Complete frontend documentation, installation, and usage
- **[Integration Guide](INTEGRATION_GUIDE.md)** - Backend API integration and setup
- **[System Verification](SYSTEM_VERIFICATION.md)** - Build verification checklist

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your backend API URL

# Start development server
npm run dev

# Access at http://localhost:3000
```

## ✨ Key Features

- ✅ Modern Next.js 16 with Turbopack
- ✅ TypeScript for type safety
- ✅ Tailwind CSS styling
- ✅ Role-based access control
- ✅ Performance optimized (SSR/SSG)
- ✅ Responsive design
- ✅ Toast notifications

## 📁 Project Structure

```
src/
├── app/              # Next.js pages
├── components/       # React components
├── hooks/           # Custom React hooks
├── lib/             # Utilities (API client)
└── types/           # TypeScript definitions
```

## 🔧 Configuration

### Environment Variables (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXTAUTH_URL=http://localhost:3000
```

## 📦 Technologies

- Next.js 16 (Turbopack)
- React 19
- TypeScript
- Tailwind CSS
- Axios
- React Hot Toast

## 🌐 Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## 📖 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)

## 🛠️ Available Commands

```bash
npm run dev        # Start dev server
npm run build      # Build for production
npm start          # Start production server
npm run lint       # Run ESLint
```

---

**Status**: Production Ready ✅
## Frontend Setup Complete! 🎉

Your Next.js hospital management frontend is ready. For detailed setup and backend integration instructions, see the documentation files above.

**Current Status**:
- ✅ Development Server: Running on http://localhost:3000
- ✅ Build Status: Successful
- ✅ No Errors: All pages compiling
- ✅ Ready to Integrate: Backend API integration guide available

See **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** to connect your Django backend.
