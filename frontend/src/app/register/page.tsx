'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

const inputClass =
  'w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-teal-400 focus:bg-white focus:ring-4 focus:ring-teal-100';

const selectClass =
  'w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-teal-400 focus:bg-white focus:ring-4 focus:ring-teal-100';

const bloodGroupOptions = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    dateOfBirth: '',
    gender: '',
    bloodGroup: '',
    address: '',
    emergencyContact: '',
    height: '',
    weight: '',
    password: '',
    confirmPassword: '',
  });

  const updateField = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm((current) => ({ ...current, [field]: event.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLoading) return;

    const requiredFields = [
      form.firstName,
      form.lastName,
      form.email,
      form.phone,
      form.dateOfBirth,
      form.gender,
      form.bloodGroup,
      form.address,
      form.emergencyContact,
      form.password,
      form.confirmPassword,
    ];

    if (requiredFields.some((value) => !value.trim())) {
      toast.error('Please fill all required patient details');
      return;
    }

    if (form.password !== form.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    try {
      setIsLoading(true);
      await apiClient.post('/auth/register/', {
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        role: 'PATIENT',
        phone: form.phone,
        date_of_birth: form.dateOfBirth,
        gender: form.gender,
        blood_group: form.bloodGroup,
        address: form.address,
        emergency_contact: form.emergencyContact,
        height: form.height,
        weight: form.weight,
      });
      toast.success('Registration successful. Please login.');
      router.push('/login');
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-[radial-gradient(circle_at_top_left,#ecfeff_0%,#eff6ff_38%,#f8fafc_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="absolute left-0 top-0 h-64 w-64 rounded-full bg-teal-300/20 blur-3xl" />
      <div className="absolute bottom-0 right-0 h-72 w-72 rounded-full bg-indigo-300/20 blur-3xl" />

      <div className="relative mx-auto w-full max-w-4xl overflow-hidden rounded-[2rem] border border-white/70 bg-white/95 shadow-[0_30px_100px_rgba(15,23,42,0.18)]">
        <section className="p-6 sm:p-8 lg:p-10">
          <div className="mx-auto max-w-2xl">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-sm font-bold uppercase tracking-[0.22em] text-teal-700">New account</p>
                <h2 className="mt-2 text-3xl font-black text-slate-950">Register as a patient</h2>
              </div>
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-800"
              >
                Sign in
              </button>
            </div>

            <form onSubmit={handleSubmit} className="mt-8 space-y-6">
              <section className="space-y-4 rounded-3xl border border-slate-200 bg-slate-50/80 p-5">
                <div>
                  <h3 className="text-lg font-bold text-slate-950">Account details</h3>
                  <p className="mt-1 text-sm text-slate-500">Basic information used to create your login.</p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">First name *</label>
                    <input
                      type="text"
                      placeholder="Enter first name"
                      value={form.firstName}
                      onChange={updateField('firstName')}
                      className={inputClass}
                      autoComplete="given-name"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Last name *</label>
                    <input
                      type="text"
                      placeholder="Enter last name"
                      value={form.lastName}
                      onChange={updateField('lastName')}
                      className={inputClass}
                      autoComplete="family-name"
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Email address *</label>
                    <input
                      type="email"
                      placeholder="patient@example.com"
                      value={form.email}
                      onChange={updateField('email')}
                      className={inputClass}
                      autoComplete="email"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Phone number *</label>
                    <input
                      type="tel"
                      placeholder="98XXXXXXXX"
                      value={form.phone}
                      onChange={updateField('phone')}
                      className={inputClass}
                      autoComplete="tel"
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Password *</label>
                    <input
                      type="password"
                      placeholder="Create a strong password"
                      value={form.password}
                      onChange={updateField('password')}
                      className={inputClass}
                      autoComplete="new-password"
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Confirm password *</label>
                    <input
                      type="password"
                      placeholder="Repeat password"
                      value={form.confirmPassword}
                      onChange={updateField('confirmPassword')}
                      className={inputClass}
                      autoComplete="new-password"
                    />
                  </div>
                </div>
              </section>

              <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
                <div>
                  <h3 className="text-lg font-bold text-slate-950">Patient profile details</h3>
                  <p className="mt-1 text-sm text-slate-500">These details help doctors, reception, and billing staff identify the patient correctly.</p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Date of birth *</label>
                    <input
                      type="date"
                      value={form.dateOfBirth}
                      onChange={updateField('dateOfBirth')}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Gender *</label>
                    <select value={form.gender} onChange={updateField('gender')} className={selectClass}>
                      <option value="">Select gender</option>
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Blood group *</label>
                    <select value={form.bloodGroup} onChange={updateField('bloodGroup')} className={selectClass}>
                      <option value="">Select blood group</option>
                      {bloodGroupOptions.map((group) => (
                        <option key={group} value={group}>
                          {group}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Emergency contact *</label>
                    <input
                      type="tel"
                      placeholder="Emergency contact number"
                      value={form.emergencyContact}
                      onChange={updateField('emergencyContact')}
                      className={inputClass}
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Height (cm)</label>
                    <input
                      type="number"
                      placeholder="Optional"
                      value={form.height}
                      onChange={updateField('height')}
                      className={inputClass}
                    />
                  </div>
                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700">Weight (kg)</label>
                    <input
                      type="number"
                      placeholder="Optional"
                      value={form.weight}
                      onChange={updateField('weight')}
                      className={inputClass}
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700">Address *</label>
                  <textarea
                    rows={4}
                    placeholder="Enter full address"
                    value={form.address}
                    onChange={updateField('address')}
                    className={inputClass}
                  />
                </div>
              </section>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="inline-flex items-center justify-center rounded-2xl bg-teal-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-teal-900/20 transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isLoading ? 'Creating account...' : 'Create patient account'}
                </button>
                <button
                  type="button"
                  onClick={() => router.push('/login')}
                  className="inline-flex items-center justify-center rounded-2xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:border-teal-200 hover:bg-teal-50 hover:text-teal-800"
                >
                  Already have an account?
                </button>
              </div>
            </form>
          </div>
        </section>
      </div>
    </div>
  );
}
