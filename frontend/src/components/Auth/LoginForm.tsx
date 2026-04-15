'use client';

import React, { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { AuthResponse } from '@/types';

export default function LoginForm() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [pendingEmail, setPendingEmail] = useState('');

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading) return;
    setIsLoading(true);

    try {
      const response = await apiClient.post<AuthResponse>('/auth/login/', { email, password });

      // Check if 2FA is required (response has no token)
      if (!response.token) {
        // 2FA required — server returned 202 with detail message
        setRequires2FA(true);
        setPendingEmail(email);
        toast.success('OTP code sent to your email. Check the terminal in development mode.');
        return;
      }

      // Store auth token and user info
      if (typeof window !== 'undefined') {
        localStorage.setItem('authToken', response.token);
        if (response.refresh) {
          localStorage.setItem('refreshToken', response.refresh);
        }
        localStorage.setItem('userRole', response.role);
        localStorage.setItem('user', JSON.stringify(response.user));
      }

      toast.success('Login successful!');
      router.push('/dashboard');
    } catch (error: any) {
      const message = error?.message || 'Login failed. Please try again.';
      toast.error(message);
      console.error('Login error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handle2FASubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading) return;
    setIsLoading(true);

    try {
      const response = await apiClient.post<AuthResponse>('/auth/2fa-verify/', {
        email: pendingEmail,
        otp: otpCode,
      });

      if (typeof window !== 'undefined') {
        localStorage.setItem('authToken', response.token);
        if (response.refresh) {
          localStorage.setItem('refreshToken', response.refresh);
        }
        localStorage.setItem('userRole', response.role);
        localStorage.setItem('user', JSON.stringify(response.user));
      }

      toast.success('Login successful!');
      router.push('/dashboard');
    } catch (error: any) {
      toast.error(error?.message || 'Invalid OTP code. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (requires2FA) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-12 sm:px-6 lg:px-8">
        <div className="w-full max-w-md space-y-8 rounded-2xl bg-white p-8 shadow-xl">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900">🔐</h1>
            <h2 className="mt-6 text-2xl font-bold text-gray-900">Two-Factor Authentication</h2>
            <p className="mt-2 text-gray-600">
              Enter the OTP code sent to <strong>{pendingEmail}</strong>
            </p>
          </div>

          <form onSubmit={handle2FASubmit} className="space-y-6">
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700">
                OTP Code
              </label>
              <input
                id="otp"
                type="text"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                required
                maxLength={6}
                className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 text-center text-2xl font-mono tracking-widest text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
                placeholder="000000"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Verifying...' : 'Verify OTP'}
            </button>

            <button
              type="button"
              onClick={() => {
                setRequires2FA(false);
                setOtpCode('');
              }}
              className="w-full text-sm text-blue-600 hover:text-blue-700"
            >
              ← Back to login
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-2xl bg-white p-8 shadow-xl">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900">🏥 HMS</h1>
          <h2 className="mt-6 text-2xl font-bold text-gray-900">Sign In</h2>
          <p className="mt-2 text-gray-600">Hospital Management System</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              name="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-2 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
              placeholder="••••••••"
            />
            <div className="mt-2 text-right">
              <button
                type="button"
                onClick={() => router.push('/forgot-password')}
                className="text-sm font-medium text-blue-600 hover:text-blue-700"
              >
                Forgot password?
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <p className="text-center text-sm text-gray-600">
          Don&apos;t have an account?{' '}
          <button
            onClick={() => router.push('/register')}
            className="font-medium text-blue-600 hover:text-blue-700"
          >
            Register here
          </button>
        </p>
      </div>
    </div>
  );
}
