'use client';

import React, { Suspense, useMemo, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

function ResetPasswordPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = searchParams?.get('user_id');
  const token = searchParams?.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const hasValidLinkData = useMemo(() => Boolean(userId && token), [userId, token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    if (!hasValidLinkData) {
      toast.error('Invalid reset link.');
      return;
    }

    if (!password || !confirmPassword) {
      toast.error('Please fill all fields');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    try {
      setIsLoading(true);
      await apiClient.post('/auth/password-reset/confirm/', {
        user_id: userId,
        token,
        password,
        confirm_password: confirmPassword,
      });
      toast.success('Password reset successful. Please login.');
      router.push('/login');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-12">
      <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
        <h1 className="text-center text-2xl font-bold text-gray-900">Reset Password</h1>

        {!hasValidLinkData ? (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            Invalid or expired reset link.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <input
              type="password"
              placeholder="New password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            />
            <input
              type="password"
              placeholder="Confirm new password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2"
            />

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isLoading ? 'Resetting...' : 'Reset Password'}
            </button>
          </form>
        )}

        <button
          type="button"
          onClick={() => router.push('/login')}
          className="mt-4 w-full text-sm text-blue-600 hover:text-blue-700"
        >
          Back to login
        </button>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 px-4 py-12">
          <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl text-gray-600">Loading reset form...</div>
        </div>
      }
    >
      <ResetPasswordPageContent />
    </Suspense>
  );
}
