'use client';

import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { extractApiErrorMessage } from '@/lib/error-utils';

type QueueStatus = 'WAITING' | 'CALLED' | 'IN_CONSULTATION' | 'COMPLETED' | 'NO_SHOW' | 'ARCHIVED';
type QueueSource = 'SCHEDULED' | 'WALK_IN' | 'REFERRAL';
type QueuePriority = 'P1' | 'P2' | 'P3' | 'P4';

interface DoctorItem {
  id: number;
  user: {
    first_name: string;
    last_name: string;
  };
}

interface QueueEntry {
  id: number;
  patient: number;
  patient_name: string;
  doctor: number;
  doctor_name: string;
  status: QueueStatus;
  source: QueueSource;
  priority: QueuePriority;
  queued_at: string;
  called_at: string | null;
  consultation_start: string | null;
  consultation_end: string | null;
  wait_time_minutes: number;
  consultation_duration_minutes: number | null;
  notes: string;
  no_show_reason: string;
  rebooking_attempted: boolean;
  rebooking_contact_date: string | null;
}

interface PatientItem {
  id: number;
  full_name: string;
  phone: string;
  user: {
    email: string;
  };
}

interface DuplicateMatch {
  patient_id: number;
  patient_name: string;
  date_of_birth: string | null;
  phone: string;
  email: string;
  match_type: string;
  confidence: number;
}

const ALL_STATUS_FILTER = 'WAITING,CALLED,IN_CONSULTATION,NO_SHOW,COMPLETED';

export default function ReceptionQueuePage() {
  const [userRole, setUserRole] = useState('');
  const [roleLoading, setRoleLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [doctors, setDoctors] = useState<DoctorItem[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | null>(null);
  const [statusFilter, setStatusFilter] = useState<'ACTIVE' | 'NO_SHOW' | 'ALL'>('ACTIVE');
  const [queueEntries, setQueueEntries] = useState<QueueEntry[]>([]);

  const [patientQuery, setPatientQuery] = useState('');
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [queueSource, setQueueSource] = useState<QueueSource>('WALK_IN');
  const [priority, setPriority] = useState<QueuePriority>('P4');
  const [notes, setNotes] = useState('');

  const [dupName, setDupName] = useState('');
  const [dupDob, setDupDob] = useState('');
  const [dupPhone, setDupPhone] = useState('');
  const [dupEmail, setDupEmail] = useState('');
  const [duplicateMatches, setDuplicateMatches] = useState<DuplicateMatch[]>([]);

  const [selectedNoShow, setSelectedNoShow] = useState<QueueEntry | null>(null);
  const [contactNotes, setContactNotes] = useState('');
  const [rebookDate, setRebookDate] = useState('');
  const [rebookTime, setRebookTime] = useState('');

  const canManage = userRole === 'RECEPTIONIST' || userRole === 'ADMIN';

  const activeCount = useMemo(
    () => queueEntries.filter((entry) => ['WAITING', 'CALLED', 'IN_CONSULTATION'].includes(entry.status)).length,
    [queueEntries]
  );

  const noShowCount = useMemo(() => queueEntries.filter((entry) => entry.status === 'NO_SHOW').length, [queueEntries]);

  const avgWaitTime = useMemo(() => {
    const waiting = queueEntries.filter((entry) => entry.status === 'WAITING');
    if (!waiting.length) return 0;
    const total = waiting.reduce((sum, entry) => sum + (entry.wait_time_minutes || 0), 0);
    return Math.round(total / waiting.length);
  }, [queueEntries]);

  useEffect(() => {
    const role = (localStorage.getItem('userRole') || '').toUpperCase();
    setUserRole(role);
    setRoleLoading(false);
  }, []);

  useEffect(() => {
    if (!canManage) return;
    loadDoctors();
  }, [canManage]);

  useEffect(() => {
    if (!canManage) return;
    loadQueue();
  }, [canManage, selectedDoctorId, statusFilter]);

  const loadDoctors = async () => {
    try {
      const response = await apiClient.get<{ results: DoctorItem[] }>('/doctors/?page_size=100');
      const doctorResults = response.results || [];
      setDoctors(doctorResults);
      if (doctorResults.length && !selectedDoctorId) {
        setSelectedDoctorId(doctorResults[0].id);
      }
    } catch (error) {
      toast.error(extractApiErrorMessage(error, 'Failed to load doctors'));
    }
  };

  const loadQueue = async () => {
    try {
      setIsLoading(true);
      const params = new URLSearchParams();
      if (selectedDoctorId) {
        params.set('doctor_id', String(selectedDoctorId));
      }
      if (statusFilter === 'NO_SHOW') {
        params.set('status', 'NO_SHOW');
      } else if (statusFilter === 'ALL') {
        params.set('status', ALL_STATUS_FILTER);
      }

      const url = params.toString() ? `/queue/?${params.toString()}` : '/queue/';
      const response = await apiClient.get<QueueEntry[]>(url);
      setQueueEntries(Array.isArray(response) ? response : []);
    } catch (error) {
      toast.error(extractApiErrorMessage(error, 'Failed to load queue'));
      setQueueEntries([]);
    } finally {
      setIsLoading(false);
    }
  };

  const searchPatients = async () => {
    if (!patientQuery.trim()) {
      setPatients([]);
      return;
    }

    try {
      const response = await apiClient.get<{ results: PatientItem[] }>(
        `/patients/?q=${encodeURIComponent(patientQuery.trim())}&page_size=8`
      );
      setPatients(response.results || []);
    } catch (error) {
      toast.error(extractApiErrorMessage(error, 'Failed to search patients'));
    }
  };

  const addToQueue = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedDoctorId || !selectedPatientId) {
      toast.error('Select doctor and patient first');
      return;
    }

    try {
      setIsSubmitting(true);
      await apiClient.post('/queue/', {
        patient_id: selectedPatientId,
        doctor_id: selectedDoctorId,
        source: queueSource,
        priority,
        notes,
      });
      toast.success('Patient added to queue');
      setSelectedPatientId(null);
      setPatientQuery('');
      setPatients([]);
      setNotes('');
      await loadQueue();
    } catch (error) {
      toast.error(extractApiErrorMessage(error, 'Failed to add patient to queue'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const updateStatus = async (entry: QueueEntry, nextStatus: QueueStatus) => {
    try {
      const payload: Record<string, string> = { status: nextStatus };
      if (nextStatus === 'NO_SHOW') {
        const reason = window.prompt('No-show reason (optional):') || '';
        if (reason.trim()) {
          payload.no_show_reason = reason.trim();
        }
      }

      await apiClient.patch(`/queue/${entry.id}/status/`, payload);
      toast.success(`Status updated to ${nextStatus}`);
      await loadQueue();
    } catch (error) {
      toast.error(extractApiErrorMessage(error, 'Failed to update queue status'));
    }
  };

  const checkDuplicate = async (event: FormEvent) => {
    event.preventDefault();
    if (!dupName.trim() || !dupDob) {
      toast.error('Name and DOB are required');
      return;
    }

    try {
      const params = new URLSearchParams({
        full_name: dupName.trim(),
        date_of_birth: dupDob,
      });
      if (dupPhone.trim()) params.set('phone', dupPhone.trim());
      if (dupEmail.trim()) params.set('email', dupEmail.trim());

      const response = await apiClient.get<{ matches: DuplicateMatch[] }>(`/queue/check-duplicate/?${params.toString()}`);
      setDuplicateMatches(response.matches || []);
      if (!response.matches?.length) {
        toast.success('No likely duplicates found');
      }
    } catch (error) {
      toast.error(extractApiErrorMessage(error, 'Failed to check duplicate patients'));
    }
  };

  const submitNoShowAction = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedNoShow) return;

    try {
      setIsSubmitting(true);
      const payload: Record<string, string> = {
        contact_notes: contactNotes,
      };
      if (rebookDate && rebookTime) {
        payload.rebook_date = rebookDate;
        payload.rebook_time = rebookTime;
      }

      await apiClient.post(`/queue/${selectedNoShow.id}/rebook/`, payload);
      toast.success('No-show follow-up recorded');
      setSelectedNoShow(null);
      setContactNotes('');
      setRebookDate('');
      setRebookTime('');
      await loadQueue();
    } catch (error) {
      toast.error(extractApiErrorMessage(error, 'Failed to save no-show action'));
    } finally {
      setIsSubmitting(false);
    }
  };

  if (roleLoading) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center text-gray-600">Loading...</div>
      </MainLayout>
    );
  }

  if (!canManage) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <p className="text-sm text-gray-500">Reception queue operations are available for admin/receptionist only.</p>
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
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Reception Queue Board</h1>
            <p className="mt-1 text-sm text-gray-600">Run check-in, queue calling, and no-show recovery from one screen.</p>
          </div>
          <button
            onClick={loadQueue}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Refresh
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <p className="text-xs uppercase tracking-wide text-blue-700">Active Queue</p>
            <p className="mt-2 text-3xl font-bold text-blue-900">{activeCount}</p>
          </div>
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
            <p className="text-xs uppercase tracking-wide text-amber-700">Average Wait</p>
            <p className="mt-2 text-3xl font-bold text-amber-900">{avgWaitTime} min</p>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50 p-4">
            <p className="text-xs uppercase tracking-wide text-red-700">No-Show Cases</p>
            <p className="mt-2 text-3xl font-bold text-red-900">{noShowCount}</p>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-5 shadow-sm xl:col-span-1">
            <h2 className="text-lg font-semibold text-gray-900">Check-In and Queue Add</h2>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Doctor</label>
              <select
                value={selectedDoctorId || ''}
                onChange={(e) => setSelectedDoctorId(e.target.value ? Number(e.target.value) : null)}
                className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
              >
                {doctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    Dr. {doctor.user.first_name} {doctor.user.last_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Search Patient</label>
              <div className="flex gap-2">
                <input
                  value={patientQuery}
                  onChange={(e) => setPatientQuery(e.target.value)}
                  placeholder="Name, email, phone"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
                <button
                  type="button"
                  onClick={searchPatients}
                  className="rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-900"
                >
                  Find
                </button>
              </div>

              {patients.length > 0 && (
                <div className="mt-2 max-h-40 overflow-auto rounded border border-gray-200">
                  {patients.map((patient) => (
                    <button
                      key={patient.id}
                      type="button"
                      onClick={() => setSelectedPatientId(patient.id)}
                      className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm ${
                        selectedPatientId === patient.id ? 'bg-blue-50 text-blue-800' : 'hover:bg-gray-50 text-gray-700'
                      }`}
                    >
                      <span>{patient.full_name}</span>
                      <span className="text-xs">{patient.phone || patient.user.email}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <form onSubmit={addToQueue} className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Source</label>
                  <select
                    value={queueSource}
                    onChange={(e) => setQueueSource(e.target.value as QueueSource)}
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
                  >
                    <option value="WALK_IN">WALK_IN</option>
                    <option value="SCHEDULED">SCHEDULED</option>
                    <option value="REFERRAL">REFERRAL</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value as QueuePriority)}
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
                  >
                    <option value="P1">P1</option>
                    <option value="P2">P2</option>
                    <option value="P3">P3</option>
                    <option value="P4">P4</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={2}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !selectedPatientId || !selectedDoctorId}
                className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
              >
                Add to Queue
              </button>
            </form>
          </section>

          <section className="space-y-4 rounded-lg border border-gray-200 bg-white p-5 shadow-sm xl:col-span-2">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-semibold text-gray-900">Queue Timeline</h2>
              <div className="flex gap-2">
                <button
                  onClick={() => setStatusFilter('ACTIVE')}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                    statusFilter === 'ACTIVE' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  Active
                </button>
                <button
                  onClick={() => setStatusFilter('NO_SHOW')}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                    statusFilter === 'NO_SHOW' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  No-Show
                </button>
                <button
                  onClick={() => setStatusFilter('ALL')}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium ${
                    statusFilter === 'ALL' ? 'bg-slate-800 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  All
                </button>
              </div>
            </div>

            {isLoading ? (
              <div className="rounded border border-gray-200 bg-gray-50 p-8 text-center text-gray-600">Loading queue...</div>
            ) : queueEntries.length === 0 ? (
              <div className="rounded border border-gray-200 bg-gray-50 p-8 text-center text-gray-600">No queue entries found.</div>
            ) : (
              <div className="space-y-3">
                {queueEntries.map((entry) => (
                  <div key={entry.id} className="rounded-lg border border-gray-200 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-base font-semibold text-gray-900">{entry.patient_name}</p>
                        <p className="text-sm text-gray-600">{entry.doctor_name}</p>
                        <p className="text-xs text-gray-500">
                          Source: {entry.source} | Wait: {entry.wait_time_minutes} min | Priority: {entry.priority}
                        </p>
                      </div>
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${
                          entry.status === 'WAITING'
                            ? 'bg-blue-100 text-blue-700'
                            : entry.status === 'CALLED'
                            ? 'bg-indigo-100 text-indigo-700'
                            : entry.status === 'IN_CONSULTATION'
                            ? 'bg-amber-100 text-amber-700'
                            : entry.status === 'NO_SHOW'
                            ? 'bg-red-100 text-red-700'
                            : 'bg-green-100 text-green-700'
                        }`}
                      >
                        {entry.status}
                      </span>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      {entry.status === 'WAITING' && (
                        <button
                          onClick={() => updateStatus(entry, 'CALLED')}
                          className="rounded border border-blue-300 bg-blue-50 px-2.5 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100"
                        >
                          Call Patient
                        </button>
                      )}

                      {entry.status === 'CALLED' && (
                        <button
                          onClick={() => updateStatus(entry, 'IN_CONSULTATION')}
                          className="rounded border border-amber-300 bg-amber-50 px-2.5 py-1.5 text-xs font-medium text-amber-700 hover:bg-amber-100"
                        >
                          Start Consultation
                        </button>
                      )}

                      {entry.status === 'IN_CONSULTATION' && (
                        <button
                          onClick={() => updateStatus(entry, 'COMPLETED')}
                          className="rounded border border-green-300 bg-green-50 px-2.5 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100"
                        >
                          Complete
                        </button>
                      )}

                      {['WAITING', 'CALLED'].includes(entry.status) && (
                        <button
                          onClick={() => updateStatus(entry, 'NO_SHOW')}
                          className="rounded border border-red-300 bg-red-50 px-2.5 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100"
                        >
                          Mark No-Show
                        </button>
                      )}

                      {entry.status === 'NO_SHOW' && (
                        <>
                          <button
                            onClick={() => setSelectedNoShow(entry)}
                            className="rounded border border-indigo-300 bg-indigo-50 px-2.5 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
                          >
                            Rebook / Contact
                          </button>
                          <button
                            onClick={() => updateStatus(entry, 'ARCHIVED')}
                            className="rounded border border-gray-300 bg-gray-50 px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-100"
                          >
                            Archive
                          </button>
                        </>
                      )}
                    </div>

                    {entry.no_show_reason && (
                      <p className="mt-2 text-xs text-red-700">Reason: {entry.no_show_reason}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Duplicate Patient Prevention</h2>
            <form onSubmit={checkDuplicate} className="mt-3 space-y-3">
              <input
                value={dupName}
                onChange={(e) => setDupName(e.target.value)}
                placeholder="Full name"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
              />
              <input
                value={dupDob}
                onChange={(e) => setDupDob(e.target.value)}
                type="date"
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
              />
              <div className="grid grid-cols-2 gap-3">
                <input
                  value={dupPhone}
                  onChange={(e) => setDupPhone(e.target.value)}
                  placeholder="Phone (optional)"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
                <input
                  value={dupEmail}
                  onChange={(e) => setDupEmail(e.target.value)}
                  placeholder="Email (optional)"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>
              <button
                type="submit"
                className="w-full rounded-md bg-slate-800 px-3 py-2 text-sm font-semibold text-white hover:bg-slate-900"
              >
                Check Duplicate Risk
              </button>
            </form>

            <div className="mt-4 space-y-2">
              {duplicateMatches.map((match) => (
                <div key={`${match.patient_id}-${match.match_type}`} className="rounded border border-amber-200 bg-amber-50 p-3">
                  <p className="text-sm font-semibold text-amber-900">{match.patient_name}</p>
                  <p className="text-xs text-amber-800">
                    {match.match_type} | Confidence {(match.confidence * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-amber-700">{match.phone || match.email || 'No contact info'}</p>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">No-Show Action Panel</h2>
            {selectedNoShow ? (
              <form onSubmit={submitNoShowAction} className="mt-3 space-y-3">
                <p className="text-sm text-gray-700">
                  Selected: <span className="font-semibold">{selectedNoShow.patient_name}</span>
                </p>
                <textarea
                  value={contactNotes}
                  onChange={(e) => setContactNotes(e.target.value)}
                  placeholder="Contact notes"
                  rows={3}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="date"
                    value={rebookDate}
                    onChange={(e) => setRebookDate(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
                  />
                  <input
                    type="time"
                    value={rebookTime}
                    onChange={(e) => setRebookTime(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900"
                  />
                </div>
                <p className="text-xs text-gray-500">If date/time is empty, this records contact attempt only.</p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedNoShow(null);
                      setContactNotes('');
                      setRebookDate('');
                      setRebookTime('');
                    }}
                    className="w-1/2 rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Clear
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-1/2 rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-400"
                  >
                    Save Action
                  </button>
                </div>
              </form>
            ) : (
              <div className="mt-3 rounded border border-dashed border-gray-300 bg-gray-50 p-6 text-sm text-gray-600">
                Select a NO_SHOW queue entry and click Rebook / Contact to manage follow-up.
              </div>
            )}
          </section>
        </div>
      </div>
    </MainLayout>
  );
}
