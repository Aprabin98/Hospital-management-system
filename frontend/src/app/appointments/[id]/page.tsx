'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface AppointmentDetail {
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
  created_at?: string;
}

interface PrescriptionListResponse {
  results: Array<{
    id: number;
    appointment: number;
  }>;
}

interface NursingNoteItem {
  id: number;
  triage_tag: string;
  note: string;
  created_at: string;
  nurse_name: string | null;
}

interface NursingTaskItem {
  id: number;
  title: string;
  details: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'DONE';
  due_at: string | null;
  assigned_to_name: string | null;
}

export default function AppointmentDetailPage() {
  const params = useParams<{ id: string }>();
  const appointmentId = Number(params?.id);

  const [appointment, setAppointment] = useState<AppointmentDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [existingPrescriptionId, setExistingPrescriptionId] = useState<number | null>(null);
  const [nursingNotes, setNursingNotes] = useState<NursingNoteItem[]>([]);
  const [nursingTasks, setNursingTasks] = useState<NursingTaskItem[]>([]);

  const userRole = useMemo(() => {
    if (typeof window === 'undefined') {
      return null;
    }
    return localStorage.getItem('userRole');
  }, []);

  const role = (userRole || '').toUpperCase();
  const isDoctorRole = role === 'DOCTOR';
  const isNurseRole = role === 'NURSE';
  const canManageStatus = role === 'DOCTOR' || role === 'RECEPTIONIST' || role === 'ADMIN';
  const isPatientRole = (userRole || '').toUpperCase() === 'PATIENT';
  const canCancelForPatient =
    isPatientRole && appointment?.status !== 'COMPLETED' && appointment?.status !== 'CANCELLED';

  const canViewNurseHandoff = isDoctorRole || isNurseRole || role === 'ADMIN';

  useEffect(() => {
    if (!appointmentId || Number.isNaN(appointmentId)) {
      setIsLoading(false);
      return;
    }

    const run = async () => {
      try {
        setIsLoading(true);
        const data = await apiClient.get<AppointmentDetail>(`/appointments/${appointmentId}/`);
        setAppointment(data);

        if (data.status === 'COMPLETED') {
          const prescriptions = await apiClient.get<PrescriptionListResponse>('/prescriptions/?page_size=200');
          const matched = (prescriptions.results || []).find((item) => item.appointment === data.id);
          setExistingPrescriptionId(matched?.id ?? null);
        }

        if (canViewNurseHandoff) {
          const [notesResponse, tasksResponse] = await Promise.all([
            apiClient.get<{ results: NursingNoteItem[] }>(`/nurse/notes/?appointment_id=${data.id}`),
            apiClient.get<{ results: NursingTaskItem[] }>(`/nurse/tasks/?appointment_id=${data.id}`),
          ]);
          setNursingNotes(notesResponse.results || []);
          setNursingTasks(tasksResponse.results || []);
        }
      } catch (err: any) {
        toast.error(err?.message || 'Failed to load appointment details');
      } finally {
        setIsLoading(false);
      }
    };

    run();
  }, [appointmentId, canViewNurseHandoff]);

  const updateStatus = async (status: AppointmentDetail['status']) => {
    if (!appointment) {
      return;
    }

    try {
      setIsUpdating(true);
      const updated = await apiClient.patch<AppointmentDetail>(`/appointments/${appointment.id}/update/`, { status });
      setAppointment(updated);
      toast.success(`Appointment marked as ${status.toLowerCase()}`);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to update appointment status');
    } finally {
      setIsUpdating(false);
    }
  };

  const downloadPdf = async (viewInBrowser = false) => {
    if (!appointment) {
      return;
    }

    try {
      const token = localStorage.getItem('authToken');
      const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/appointments/${appointment.id}/download-pdf/`, {
        method: 'GET',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        let message = 'Failed to fetch appointment PDF';
        try {
          const payload = await response.json();
          message = payload?.detail || payload?.message || message;
        } catch {
          // Ignore non-JSON error body.
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      if (viewInBrowser) {
        const popup = window.open(url, '_blank', 'noopener,noreferrer');
        if (!popup) {
          window.location.href = url;
        }
      } else {
        const a = document.createElement('a');
        a.href = url;
        a.download = `appointment_${appointment.id}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }

      window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to fetch appointment PDF');
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex h-64 items-center justify-center text-gray-600">Loading appointment details...</div>
      </MainLayout>
    );
  }

  if (!appointment) {
    return (
      <MainLayout>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">Appointment not found.</div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Appointment Detail</h1>
            <p className="mt-1 text-sm text-gray-600">Review appointment and take next actions.</p>
          </div>
          <Link href="/appointments" className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            Back to Appointments
          </Link>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs uppercase text-gray-500">Patient</p>
              <p className="text-base font-semibold text-gray-900">{appointment.patient_name}</p>
            </div>
            <div>
              <p className="text-xs uppercase text-gray-500">Doctor</p>
              <p className="text-base font-semibold text-gray-900">{appointment.doctor_name}</p>
            </div>
            <div>
              <p className="text-xs uppercase text-gray-500">Date</p>
              <p className="text-base text-gray-900">{appointment.date}</p>
            </div>
            <div>
              <p className="text-xs uppercase text-gray-500">Time</p>
              <p className="text-base text-gray-900">
                {appointment.start_time} - {appointment.end_time}
              </p>
            </div>
            <div>
              <p className="text-xs uppercase text-gray-500">Status</p>
              <p className="text-base font-semibold text-gray-900">{appointment.status}</p>
            </div>
            <div>
              <p className="text-xs uppercase text-gray-500">Appointment ID</p>
              <p className="text-base text-gray-900">#{appointment.id}</p>
            </div>
          </div>

          <div className="mt-5">
            <p className="text-xs uppercase text-gray-500">Notes</p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-gray-700">{appointment.notes || 'No notes provided.'}</p>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => downloadPdf(true)}
              className="rounded-lg border border-indigo-300 bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-100"
            >
              View Appointment PDF
            </button>
            <button
              type="button"
              onClick={() => downloadPdf(false)}
              className="rounded-lg border border-green-300 bg-green-50 px-4 py-2 text-sm font-semibold text-green-700 hover:bg-green-100"
            >
              Download Appointment PDF
            </button>
          </div>
        </div>

        {(canManageStatus || canCancelForPatient) && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Actions</h2>
            <div className="mt-4 flex flex-wrap gap-3">
              {canCancelForPatient && (
                <button
                  type="button"
                  onClick={() => updateStatus('CANCELLED')}
                  disabled={isUpdating}
                  className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:bg-red-300"
                >
                  Cancel Appointment
                </button>
              )}

              {canManageStatus && appointment.status !== 'COMPLETED' && appointment.status !== 'CANCELLED' && (
                <>
                  <button
                    type="button"
                    onClick={() => updateStatus('COMPLETED')}
                    disabled={isUpdating}
                    className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:bg-green-300"
                  >
                    Mark as Completed
                  </button>
                  <button
                    type="button"
                    onClick={() => updateStatus('CANCELLED')}
                    disabled={isUpdating}
                    className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:bg-red-300"
                  >
                    Cancel Appointment
                  </button>
                </>
              )}

              {isDoctorRole && appointment.status === 'COMPLETED' && !existingPrescriptionId && (
                <Link
                  href={`/prescriptions-writer?appointmentId=${appointment.id}&patientId=${appointment.patient}`}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                >
                  Write Prescription
                </Link>
              )}

              {isDoctorRole && appointment.status === 'COMPLETED' && existingPrescriptionId && (
                <Link
                  href="/prescriptions"
                  className="rounded-lg bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-100"
                >
                  Prescription Exists (ID: {existingPrescriptionId})
                </Link>
              )}
            </div>
          </div>
        )}

        {canViewNurseHandoff && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Nurse Handoff Panel</h2>
            <p className="mt-1 text-sm text-gray-600">Doctor encounter context from nurse notes and task checklist.</p>

            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold text-gray-800">Nursing Notes</h3>
                <div className="mt-2 space-y-2">
                  {nursingNotes.length === 0 ? (
                    <p className="text-sm text-gray-500">No nursing notes recorded for this appointment.</p>
                  ) : (
                    nursingNotes.map((item) => (
                      <div key={item.id} className="rounded border border-gray-200 p-3">
                        <p className="text-xs text-gray-500">{item.triage_tag} • {item.nurse_name || 'Nurse'} • {new Date(item.created_at).toLocaleString()}</p>
                        <p className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">{item.note}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-800">Nursing Tasks</h3>
                <div className="mt-2 space-y-2">
                  {nursingTasks.length === 0 ? (
                    <p className="text-sm text-gray-500">No nursing tasks for this appointment.</p>
                  ) : (
                    nursingTasks.map((item) => (
                      <div key={item.id} className="rounded border border-gray-200 p-3">
                        <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                        <p className="text-xs text-gray-500">{item.status} {item.assigned_to_name ? `• ${item.assigned_to_name}` : ''}</p>
                        <p className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">{item.details || 'No details provided.'}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {isPatientRole && appointment.status === 'COMPLETED' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Feedback</h2>
            <p className="mt-2 text-sm text-gray-600">Share your consultation experience for this completed appointment.</p>
            <Link
              href={`/reviews?appointmentId=${appointment.id}`}
              className="mt-4 inline-block rounded-lg bg-yellow-500 px-4 py-2 text-sm font-semibold text-white hover:bg-yellow-600"
            >
              Write Review
            </Link>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
