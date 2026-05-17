'use client';

import React, { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { setStoredAuthState } from '@/lib/auth';
import { AuthResponse } from '@/types';

export default function LoginForm() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [requires2FA, setRequires2FA] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [pendingEmail, setPendingEmail] = useState('');

  const saveAuth = (response: AuthResponse) => {
    setStoredAuthState({
      token: response.token,
      refreshToken: response.refresh || null,
      role: response.role,
      user: response.user,
    });
    toast.success('Login successful');
    router.push('/dashboard');
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLoading) return;
    setIsLoading(true);
    try {
      const response = await apiClient.post<AuthResponse>('/auth/login/', { email, password });
      if (!response.token) {
        setRequires2FA(true);
        setPendingEmail(email);
        toast.success('OTP code sent to your email');
        return;
      }
      saveAuth(response);
    } catch (error: any) {
      toast.error(error?.message || 'Login failed');
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
      saveAuth(response);
    } catch (error: any) {
      toast.error(error?.message || 'Invalid OTP code');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[linear-gradient(135deg,#ecfeff_0%,#f8fafc_48%,#eef2ff_100%)] px-4 py-12">
      <div className="w-full max-w-md rounded-2xl border border-white bg-white/95 p-8 shadow-[0_24px_70px_rgba(15,23,42,0.12)]">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-teal-700 text-xl font-black text-white">
            M
          </div>
          <h1 className="mt-5 text-3xl font-black text-gray-950">MediMind</h1>
          <p className="mt-2 text-sm text-gray-600">Hospital and patient management workspace</p>
        </div>

        {requires2FA ? (
          <form onSubmit={handle2FASubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="otp" className="block text-sm font-medium text-gray-700">OTP Code</label>
              <input
                id="otp"
                type="text"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                required
                maxLength={6}
                className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 text-center text-xl tracking-widest text-gray-900 focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
                placeholder="000000"
              />
              <p className="mt-2 text-xs text-gray-500">Enter the verification code sent to {pendingEmail}.</p>
            </div>
            <button disabled={isLoading} className="w-full rounded-lg bg-teal-700 px-4 py-3 font-semibold text-white hover:bg-teal-800 disabled:opacity-50">
              {isLoading ? 'Verifying...' : 'Verify OTP'}
            </button>
            <button type="button" onClick={() => setRequires2FA(false)} className="w-full text-sm font-medium text-teal-700">
              Back to login
            </button>
          </form>
        ) : (
          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email Address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-2 w-full rounded-lg border border-gray-300 px-4 py-3 text-gray-900 focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
                placeholder="Enter your password"
              />
              <div className="mt-2 text-right">
                <button type="button" onClick={() => router.push('/forgot-password')} className="text-sm font-medium text-teal-700">
                  Forgot password?
                </button>
              </div>
            </div>
            <button disabled={isLoading} className="w-full rounded-lg bg-teal-700 px-4 py-3 font-semibold text-white hover:bg-teal-800 disabled:opacity-50">
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        )}

        <p className="mt-6 text-center text-sm text-gray-600">
          Need an account?{' '}
          <button onClick={() => router.push('/register')} className="font-medium text-teal-700">
            Register here
          </button>
        </p>
      </div>
    </div>
  );
}
