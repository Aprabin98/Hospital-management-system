'use client';

import React, { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { PaginatedResponse } from '@/types';
import { apiClient } from '@/lib/api';

interface AppointmentRow {
  id: number;
  patient: number;
  patient_name: string;
  doctor: number;
  doctor_name: string;
  date: string;
  start_time: string;
  end_time: string;
  status: 'PENDING' | 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
  notes?: string;
}

type FilterKey = 'ACTIVE' | 'ALL' | 'COMPLETED' | 'CANCELLED';

const getErrorMessage = (err: unknown, fallback: string) => {
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return fallback;
};

function AppointmentsPageContent() {
  const searchParams = useSearchParams();
  const [appointments, setAppointments] = useState<AppointmentRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUpdatingId, setIsUpdatingId] = useState<number | null>(null);
  const [filter, setFilter] = useState<FilterKey>(() => {
    const initialFilter = (searchParams?.get('filter') || '').toUpperCase();
    if (initialFilter === 'ALL' || initialFilter === 'COMPLETED' || initialFilter === 'CANCELLED' || initialFilter === 'ACTIVE') {
      return initialFilter;
    }
    return 'ACTIVE';
  });
  const [userRole, setUserRole] = useState('');
  const isDoctor = userRole === 'DOCTOR';
  const isReceptionist = userRole === 'RECEPTIONIST';
  const isAdmin = userRole === 'ADMIN';
  const isPatient = userRole === 'PATIENT';
  const canManageStatus = isDoctor || isReceptionist || isAdmin;

  useEffect(() => {
    fetchAppointments();
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
  }, []);

  const fetchAppointments = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<AppointmentRow>>('/appointments/?page_size=200');
      setAppointments(response.results || []);
      setError(null);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to load appointments'));
      toast.error('Failed to load appointments');
    } finally {
      setIsLoading(false);
    }
  };

  const updateAppointmentStatus = async (appointmentId: number, status: AppointmentRow['status']) => {
    try {
      setIsUpdatingId(appointmentId);
      await apiClient.patch(`/appointments/${appointmentId}/update/`, { status });
      setAppointments((prev) =>
        prev.map((item) => (item.id === appointmentId ? { ...item, status } : item))
      );
      toast.success(`Appointment marked as ${status.toLowerCase()}`);
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Failed to update appointment status'));
    } finally {
      setIsUpdatingId(null);
    }
  };

  const filteredAppointments = appointments.filter((appointment) => {
    if (filter === 'ACTIVE') {
      return appointment.status !== 'COMPLETED';
    }
    if (filter === 'COMPLETED') {
      return appointment.status === 'COMPLETED';
    }
    if (filter === 'CANCELLED') {
      return appointment.status === 'CANCELLED';
    }
    return true;
  });

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Appointments</h1>
            <p className="mt-2 text-gray-600">
              {isPatient ? 'View and manage your appointments' : 'Schedule and manage appointments'}
            </p>
          </div>
          {userRole !== 'DOCTOR' && (
            <Link
              href="/appointments/create"
              className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white transition-colors hover:bg-blue-700"
            >
              + New Appointment
            </Link>
          )}
        </div>

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg text-gray-600">Loading appointments...</div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {!isLoading && (
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setFilter('ACTIVE')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                filter === 'ACTIVE' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Active (hide completed)
            </button>
            <button
              type="button"
              onClick={() => setFilter('ALL')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                filter === 'ALL' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              All
            </button>
            <button
              type="button"
              onClick={() => setFilter('COMPLETED')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                filter === 'COMPLETED' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Completed
            </button>
            <button
              type="button"
              onClick={() => setFilter('CANCELLED')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                filter === 'CANCELLED' ? 'bg-blue-600 text-white' : 'bg-white text-gray-700 border border-gray-300'
              }`}
            >
              Cancelled
            </button>
          </div>
        )}

        {!isLoading && filteredAppointments.length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
            <p className="text-gray-600">No appointments found for this filter</p>
          </div>
        )}

        {!isLoading && filteredAppointments.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {!isPatient && <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Patient</th>}
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Doctor</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Time</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredAppointments.map((appointment) => (
                  <tr key={appointment.id} className="hover:bg-gray-50">
                    {!isPatient && <td className="px-6 py-4 text-sm text-gray-900">{appointment.patient_name}</td>}
                    <td className="px-6 py-4 text-sm text-gray-600">{appointment.doctor_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{appointment.date}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{appointment.start_time}</td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${getStatusBadgeColor(
                          appointment.status.toLowerCase()
                        )}`}
                      >
                        {appointment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <Link
                        href={`/appointments/${appointment.id}`}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        View
                      </Link>

                      {isPatient && appointment.status !== 'COMPLETED' && appointment.status !== 'CANCELLED' && (
                        <button
                          type="button"
                          onClick={() => updateAppointmentStatus(appointment.id, 'CANCELLED')}
                          disabled={isUpdatingId === appointment.id}
                          className="ml-3 text-red-600 hover:text-red-700 disabled:text-gray-400"
                        >
                          Cancel
                        </button>
                      )}

                      {canManageStatus && appointment.status !== 'COMPLETED' && appointment.status !== 'CANCELLED' && (
                        <>
                          <button
                            type="button"
                            onClick={() => updateAppointmentStatus(appointment.id, 'COMPLETED')}
                            disabled={isUpdatingId === appointment.id}
                            className="ml-3 text-green-600 hover:text-green-700 disabled:text-gray-400"
                          >
                            Mark Complete
                          </button>
                          <button
                            type="button"
                            onClick={() => updateAppointmentStatus(appointment.id, 'CANCELLED')}
                            disabled={isUpdatingId === appointment.id}
                            className="ml-3 text-red-600 hover:text-red-700 disabled:text-gray-400"
                          >
                            Cancel
                          </button>
                        </>
                      )}

                      {isDoctor && appointment.status === 'COMPLETED' && (
                        <Link
                          href={`/prescriptions-writer?appointmentId=${appointment.id}&patientId=${appointment.patient}`}
                          className="ml-3 text-indigo-600 hover:text-indigo-700"
                        >
                          Prescribe
                        </Link>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </MainLayout>
  );
}

export default function AppointmentsPage() {
  return (
    <Suspense
      fallback={
        <MainLayout>
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-gray-600 shadow-sm">
            Loading appointments...
          </div>
        </MainLayout>
      }
    >
      <AppointmentsPageContent />
    </Suspense>
  );
}
