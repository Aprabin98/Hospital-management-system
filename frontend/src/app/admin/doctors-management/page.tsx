'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface Specialization {
  id: number;
  name: string;
}

interface DoctorCreateForm {
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  password: string;
  specialization: string;
  consultation_fee: string;
  experience_years: string;
  phone: string;
  bio: string;
  is_available: boolean;
}

interface DoctorUser {
  id: number;
  email: string;
  username?: string;
  first_name: string;
  last_name: string;
}

interface Doctor {
  id: number;
  user: DoctorUser;
  specialization: Specialization | null;
  consultation_fee: number;
  bio?: string;
  experience_years: number;
  is_available: boolean;
  phone?: string;
  photo?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const BACKEND_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, '');

export default function DoctorsManagementPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [specializations, setSpecializations] = useState<Specialization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAvailability, setFilterAvailability] = useState<'ALL' | 'AVAILABLE' | 'UNAVAILABLE'>('ALL');

  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);
  const [showCreateDoctor, setShowCreateDoctor] = useState(false);
  const [editingDoctorId, setEditingDoctorId] = useState<number | null>(null);
  const [isCreatingDoctor, setIsCreatingDoctor] = useState(false);
  const [doctorForm, setDoctorForm] = useState<DoctorCreateForm>({
    email: '',
    username: '',
    first_name: '',
    last_name: '',
    password: '',
    specialization: '',
    consultation_fee: '0',
    experience_years: '0',
    phone: '',
    bio: '',
    is_available: true,
  });
  const [pageSize] = useState(10);
  const [currentPage, setCurrentPage] = useState(1);

  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchDoctors();
    fetchSpecializations();
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('create') === '1') {
      setShowCreateDoctor(true);
    }
  }, []);

  const fetchDoctors = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<Doctor>>('/doctors/');
      setDoctors(response.results || []);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load doctors');
      toast.error('Failed to load doctors');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSpecializations = async () => {
    try {
      const response = await apiClient.get<{ count: number; results: Specialization[] }>('/specializations/');
      setSpecializations(response.results || []);
    } catch {
      setSpecializations([]);
    }
  };

  const resetDoctorForm = () => {
    setDoctorForm({
      email: '',
      username: '',
      first_name: '',
      last_name: '',
      password: '',
      specialization: '',
      consultation_fee: '0',
      experience_years: '0',
      phone: '',
      bio: '',
      is_available: true,
    });
  };

  const openCreateDoctor = () => {
    setEditingDoctorId(null);
    resetDoctorForm();
    setShowCreateDoctor(true);
  };

  const openEditDoctor = (doctor: Doctor) => {
    setEditingDoctorId(doctor.id);
    setDoctorForm({
      email: doctor.user.email || '',
      username: doctor.user.username || '',
      first_name: doctor.user.first_name || '',
      last_name: doctor.user.last_name || '',
      password: '',
      specialization: doctor.specialization?.id ? String(doctor.specialization.id) : '',
      consultation_fee: String(doctor.consultation_fee ?? '0'),
      experience_years: String(doctor.experience_years ?? '0'),
      phone: doctor.phone || '',
      bio: doctor.bio || '',
      is_available: doctor.is_available,
    });
    setShowCreateDoctor(true);
  };

  const closeDoctorForm = () => {
    setShowCreateDoctor(false);
    setEditingDoctorId(null);
    resetDoctorForm();
  };

  const submitDoctorForm = async () => {
    try {
      setIsCreatingDoctor(true);
      const payload = {
        ...doctorForm,
        specialization: doctorForm.specialization ? Number(doctorForm.specialization) : null,
        consultation_fee: Number(doctorForm.consultation_fee || 0),
        experience_years: Number(doctorForm.experience_years || 0),
      };
      if (editingDoctorId) {
        await apiClient.patch(`/doctors/${editingDoctorId}/`, payload);
        toast.success('Doctor updated successfully');
      } else {
        if (!doctorForm.password.trim()) {
          toast.error('Password is required for new doctors');
          return;
        }
        await apiClient.post('/doctors/create/', payload);
        toast.success('Doctor created successfully');
      }
      closeDoctorForm();
      await fetchDoctors();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : editingDoctorId ? 'Failed to update doctor' : 'Failed to create doctor');
    } finally {
      setIsCreatingDoctor(false);
    }
  };

  const handleToggleAvailability = async (doctorId: number, currentStatus: boolean) => {
    try {
      // Call backend to toggle availability
      await apiClient.patch(`/doctors/${doctorId}/`, {
        is_available: !currentStatus,
      });
      setDoctors((prev) =>
        prev.map((d) =>
          d.id === doctorId ? { ...d, is_available: !currentStatus } : d
        )
      );
      toast.success(`Doctor availability updated`);
    } catch {
      toast.error('Failed to update availability');
    }
  };

  const handleDeleteDoctor = async (doctorId: number) => {
    try {
      await apiClient.delete(`/doctors/${doctorId}/`);
      setDoctors((prev) => prev.filter((d) => d.id !== doctorId));
      setShowDeleteConfirm(null);
      toast.success('Doctor deleted successfully');
    } catch {
      toast.error('Failed to delete doctor');
    }
  };

  const filteredDoctors = useMemo(() => {
    let result = doctors;

    // Filter by search term
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (d) =>
          d.user.first_name.toLowerCase().includes(term) ||
          d.user.last_name.toLowerCase().includes(term) ||
          d.user.email.toLowerCase().includes(term) ||
          d.specialization?.name.toLowerCase().includes(term)
      );
    }

    // Filter by availability
    if (filterAvailability === 'AVAILABLE') {
      result = result.filter((d) => d.is_available);
    } else if (filterAvailability === 'UNAVAILABLE') {
      result = result.filter((d) => !d.is_available);
    }

    return result;
  }, [doctors, searchTerm, filterAvailability]);

  const paginatedDoctors = useMemo(() => {
    const startIdx = (currentPage - 1) * pageSize;
    return filteredDoctors.slice(startIdx, startIdx + pageSize);
  }, [filteredDoctors, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredDoctors.length / pageSize);

  if (!isAdmin) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <p className="text-gray-500">You do not have permission to access this page.</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Doctor Management</h1>
          <p className="mt-2 text-gray-600">Manage doctor profiles, availability, and status</p>
        </div>

        {/* Top Actions */}
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-lg bg-white p-4 shadow-sm">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Search by name, email, or specialization"
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <select
              value={filterAvailability}
              onChange={(e) => {
                setFilterAvailability(e.target.value as 'ALL' | 'AVAILABLE' | 'UNAVAILABLE');
                setCurrentPage(1);
              }}
              className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="ALL">All Doctors</option>
              <option value="AVAILABLE">Available</option>
              <option value="UNAVAILABLE">Unavailable</option>
            </select>
          </div>
          <button
            type="button"
            onClick={openCreateDoctor}
            className="inline-flex rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700"
          >
            + Add New Doctor
          </button>
        </div>

        {showCreateDoctor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4 border-b border-gray-200 pb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{editingDoctorId ? 'Edit Doctor' : 'Add New Doctor'}</h2>
                <p className="mt-1 text-sm text-gray-600">{editingDoctorId ? 'Update the doctor profile directly in the frontend UI.' : 'Create the doctor account and profile inside the frontend UI.'}</p>
              </div>
              <button onClick={closeDoctorForm} className="rounded-full border border-gray-300 px-3 py-1 text-sm text-gray-600 hover:bg-gray-50">Close</button>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="First name" value={doctorForm.first_name} onChange={(e) => setDoctorForm((prev) => ({ ...prev, first_name: e.target.value }))} />
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Last name" value={doctorForm.last_name} onChange={(e) => setDoctorForm((prev) => ({ ...prev, last_name: e.target.value }))} />
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Email" type="email" value={doctorForm.email} onChange={(e) => setDoctorForm((prev) => ({ ...prev, email: e.target.value }))} />
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Username (optional)" value={doctorForm.username} onChange={(e) => setDoctorForm((prev) => ({ ...prev, username: e.target.value }))} />
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder={editingDoctorId ? 'Password (optional for edit)' : 'Password'} type="password" value={doctorForm.password} onChange={(e) => setDoctorForm((prev) => ({ ...prev, password: e.target.value }))} />
              <select className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900" value={doctorForm.specialization} onChange={(e) => setDoctorForm((prev) => ({ ...prev, specialization: e.target.value }))}>
                <option value="">Select specialization</option>
                {specializations.map((spec) => (
                  <option key={spec.id} value={spec.id}>{spec.name}</option>
                ))}
              </select>
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Consultation fee" type="number" value={doctorForm.consultation_fee} onChange={(e) => setDoctorForm((prev) => ({ ...prev, consultation_fee: e.target.value }))} />
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Experience years" type="number" value={doctorForm.experience_years} onChange={(e) => setDoctorForm((prev) => ({ ...prev, experience_years: e.target.value }))} />
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Phone" value={doctorForm.phone} onChange={(e) => setDoctorForm((prev) => ({ ...prev, phone: e.target.value }))} />
              <label className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700">
                <input type="checkbox" checked={doctorForm.is_available} onChange={(e) => setDoctorForm((prev) => ({ ...prev, is_available: e.target.checked }))} />
                Available for appointments
              </label>
              <textarea className="md:col-span-2 min-h-28 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Bio" value={doctorForm.bio} onChange={(e) => setDoctorForm((prev) => ({ ...prev, bio: e.target.value }))} />
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={closeDoctorForm} className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50">
                Cancel
              </button>
              <button type="button" disabled={isCreatingDoctor} onClick={submitDoctorForm} className="rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-60">
                {isCreatingDoctor ? 'Saving...' : editingDoctorId ? 'Save Changes' : 'Create Doctor'}
              </button>
            </div>
          </div>
        </div>
        )}

        {/* Doctors Table */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading doctors...</div>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
        ) : filteredDoctors.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">
            No doctors found matching your criteria.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="w-full">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Doctor</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Specialization</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Experience</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Fee</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedDoctors.map((doctor) => (
                  <tr key={doctor.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        {doctor.photo && (
                          <Image
                            src={`${BACKEND_ORIGIN}${doctor.photo}`}
                            alt={`${doctor.user.first_name} ${doctor.user.last_name}`}
                            width={40}
                            height={40}
                            className="rounded-full object-cover"
                          />
                        )}
                        <div>
                          <p className="font-medium text-gray-900">
                            {doctor.user.first_name} {doctor.user.last_name}
                          </p>
                          <p className="text-sm text-gray-500">{doctor.user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {doctor.specialization?.name || 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {doctor.experience_years} years
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      ₹{doctor.consultation_fee}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => handleToggleAvailability(doctor.id, doctor.is_available)}
                        className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${
                          doctor.is_available
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {doctor.is_available ? '✓ Available' : '✗ Unavailable'}
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => openEditDoctor(doctor)}
                          className="inline-flex rounded border border-blue-300 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700 hover:bg-blue-100"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(doctor.id)}
                          className="inline-flex rounded border border-red-300 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-100"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between rounded-lg bg-white p-4 shadow-sm">
            <div className="text-sm text-gray-600">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filteredDoctors.length)} of{' '}
              {filteredDoctors.length} doctors
            </div>
            <div className="flex gap-2">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`rounded px-2 py-1 text-sm ${
                      currentPage === page
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Confirm Delete</h3>
            <p className="mt-2 text-gray-600">
              Are you sure you want to delete this doctor? This action cannot be undone.
            </p>
            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="rounded border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteDoctor(showDeleteConfirm)}
                className="rounded bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
