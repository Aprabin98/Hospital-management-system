'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks';

export default function AddPatientPage() {
  const router = useRouter();
  const { userRole } = useAuth();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  const canCreatePatient = ['admin', 'doctor', 'receptionist'].includes((userRole || '').toLowerCase());

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!firstName || !lastName || !email || !password || !confirmPassword) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.post('/auth/register/', {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
        role: 'patient',
      });

      toast.success('Patient account created successfully');
      router.push('/patients');
    } catch (err: any) {
      const message = err?.message || 'Failed to create patient account';
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Link href="/patients" className="text-blue-600 hover:text-blue-700 font-medium inline-block mb-2">
            ← Back to Patients
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Add Patient</h1>
          <p className="mt-2 text-gray-600">Create a new patient account for hospital records</p>
        </div>

        {!canCreatePatient && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-yellow-800">
            Your role does not have permission to create patients.
          </div>
        )}

        <form onSubmit={handleSubmit} className="max-w-2xl space-y-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">First Name *</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Enter first name"
                disabled={!canCreatePatient || isSaving}
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Last Name *</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Enter last name"
                disabled={!canCreatePatient || isSaving}
                required
              />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">Email *</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="patient@example.com"
              disabled={!canCreatePatient || isSaving}
              required
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Password *</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Create password"
                disabled={!canCreatePatient || isSaving}
                required
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Confirm Password *</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Confirm password"
                disabled={!canCreatePatient || isSaving}
                required
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={!canCreatePatient || isSaving}
              className="rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {isSaving ? 'Creating...' : 'Create Patient'}
            </button>
            <Link
              href="/patients"
              className="rounded-lg border border-gray-300 px-5 py-2 font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </MainLayout>
  );
}
