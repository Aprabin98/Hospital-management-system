'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Check if user has auth token
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('authToken');
      if (token) {
        router.push('/dashboard');
      } else {
        router.push('/login');
      }
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center">
        <div className="text-4xl font-bold text-gray-900">🏥 HMS</div>
        <p className="mt-4 text-gray-600">Hospital Management System</p>
        <p className="mt-2 text-sm text-gray-500">Redirecting...</p>
      </div>
    </div>
  );
}
