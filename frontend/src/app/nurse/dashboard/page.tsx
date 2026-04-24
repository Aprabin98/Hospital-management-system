'use client';

import React, { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';

interface NurseKpis {
  active_queue_count: number;
  high_priority_triage_count: number;
  pending_tasks_count: number;
  today_appointments_count: number;
}

interface NurseQueueItem {
  id: number;
  patient_id: number;
  patient_name: string;
  doctor_name: string;
  status: string;
  priority: 'P1' | 'P2' | 'P3' | 'P4';
  wait_time_minutes: number;
}

interface TriageItem {
  id: number;
  patient: number;
  patient_name: string;
  priority: 'P1' | 'P2' | 'P3' | 'P4';
  symptoms: string;
  created_at: string;
}

interface NursingTaskItem {
  id: number;
  appointment: number;
  patient: number;
  patient_name: string;
  title: string;
  details: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'DONE';
  due_at: string | null;
}

interface NursingNoteItem {
  id: number;
  appointment: number;
  patient: number;
  patient_name: string;
  triage_tag: 'P1' | 'P2' | 'P3' | 'P4';
  note: string;
  created_at: string;
  nurse_name: string | null;
}

interface PatientItem {
  id: number;
  full_name: string;
  user: {
    email: string;
  };
}

interface PatientProfile {
  id: number;
  full_name: string;
  phone: string;
  blood_group: string;
  user: {
    first_name: string;
    last_name: string;
    email: string;
  };
}

interface AllergyItem {
  id: number;
  allergen: string;
  reaction: string;
  severity: string;
  status: string;
  notes: string;
  diagnosed_on: string | null;
  updated_at: string;
}

interface VitalLogItem {
  id: number;
  blood_pressure: string;
  pulse: number | null;
  temperature_c: number | null;
  respiratory_rate: number | null;
  oxygen_saturation: number | null;
  weight_kg: number | null;
  height_cm: number | null;
  notes: string;
  recorded_at: string;
  recorded_by: number | null;
}

export default function NurseDashboardPage() {
  const { userRole, isLoading: authLoading } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const [kpis, setKpis] = useState<NurseKpis>({
    active_queue_count: 0,
    high_priority_triage_count: 0,
    pending_tasks_count: 0,
    today_appointments_count: 0,
  });
  const [queueItems, setQueueItems] = useState<NurseQueueItem[]>([]);
  const [triageItems, setTriageItems] = useState<TriageItem[]>([]);
  const [taskItems, setTaskItems] = useState<NursingTaskItem[]>([]);

  const [patientQuery, setPatientQuery] = useState('');
  const [patientOptions, setPatientOptions] = useState<PatientItem[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [selectedPatientProfile, setSelectedPatientProfile] = useState<PatientProfile | null>(null);
  const [patientAllergies, setPatientAllergies] = useState<AllergyItem[]>([]);
  const [patientVitals, setPatientVitals] = useState<VitalLogItem[]>([]);
  const [patientSafetyLoading, setPatientSafetyLoading] = useState(false);
  const [patientSafetyError, setPatientSafetyError] = useState<string | null>(null);
  const [appointmentId, setAppointmentId] = useState<number | null>(null);

  const [bp, setBp] = useState('');
  const [pulse, setPulse] = useState('');
  const [temp, setTemp] = useState('');
  const [respRate, setRespRate] = useState('');
  const [spo2, setSpo2] = useState('');
  const [vitalsNotes, setVitalsNotes] = useState('');

  const [triageTag, setTriageTag] = useState<'P1' | 'P2' | 'P3' | 'P4'>('P3');
  const [nursingNote, setNursingNote] = useState('');
  const [notesHistory, setNotesHistory] = useState<NursingNoteItem[]>([]);

  const [taskTitle, setTaskTitle] = useState('');
  const [taskDetails, setTaskDetails] = useState('');

  const role = (userRole || '').toUpperCase();
  const canAccess = useMemo(() => ['NURSE', 'ADMIN', 'DOCTOR'].includes(role), [role]);

  useEffect(() => {
    if (!canAccess) return;
    loadDashboard();
  }, [canAccess]);

  useEffect(() => {
    if (!selectedPatientId) {
      setSelectedPatientProfile(null);
      setPatientAllergies([]);
      setPatientVitals([]);
      setPatientSafetyError(null);
      return;
    }

    const loadSafetySnapshot = async () => {
      try {
        setPatientSafetyLoading(true);
        setPatientSafetyError(null);
        const [profileRes, allergyRes, vitalsRes] = await Promise.all([
          apiClient.get<PatientProfile>(`/patients/${selectedPatientId}/`),
          apiClient.get<{ count: number; results: AllergyItem[] }>(`/patients/${selectedPatientId}/allergies/`),
          apiClient.get<{ count: number; results: VitalLogItem[] }>(`/vital-logs/?patient=${selectedPatientId}&page_size=5`),
        ]);

        setSelectedPatientProfile(profileRes);
        setPatientAllergies(allergyRes.results || []);
        setPatientVitals(vitalsRes.results || []);
      } catch (err: any) {
        setSelectedPatientProfile(null);
        setPatientAllergies([]);
        setPatientVitals([]);
        setPatientSafetyError(err?.message || 'Failed to load patient safety snapshot');
      } finally {
        setPatientSafetyLoading(false);
      }
    };

    loadSafetySnapshot();
  }, [selectedPatientId]);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<{
        kpis: NurseKpis;
        queue: NurseQueueItem[];
        triage: TriageItem[];
        tasks: NursingTaskItem[];
      }>('/nurse/dashboard/');
      setKpis(response.kpis);
      setQueueItems(response.queue || []);
      setTriageItems(response.triage || []);
      setTaskItems(response.tasks || []);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load nurse dashboard');
    } finally {
      setLoading(false);
    }
  };

  const searchPatients = async () => {
    const q = patientQuery.trim();
    if (!q) {
      setPatientOptions([]);
      return;
    }
    try {
      const response = await apiClient.get<{ results: PatientItem[] }>(`/patients/?q=${encodeURIComponent(q)}&page_size=8`);
      setPatientOptions(response.results || []);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to search patients');
    }
  };

  const createVitalLog = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId) {
      toast.error('Select patient first');
      return;
    }

    try {
      setSaving(true);
      await apiClient.post('/vital-logs/', {
        patient: selectedPatientId,
        blood_pressure: bp,
        pulse: pulse ? Number(pulse) : null,
        temperature_c: temp ? Number(temp) : null,
        respiratory_rate: respRate ? Number(respRate) : null,
        oxygen_saturation: spo2 ? Number(spo2) : null,
        notes: vitalsNotes,
      });
      toast.success('Vitals recorded');
      setBp('');
      setPulse('');
      setTemp('');
      setRespRate('');
      setSpo2('');
      setVitalsNotes('');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to record vitals');
    } finally {
      setSaving(false);
    }
  };

  const createNurseNote = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId || !appointmentId || !nursingNote.trim()) {
      toast.error('Patient, appointment ID and note are required');
      return;
    }

    try {
      setSaving(true);
      await apiClient.post('/nurse/notes/', {
        appointment: appointmentId,
        patient: selectedPatientId,
        triage_tag: triageTag,
        note: nursingNote.trim(),
      });
      toast.success('Nursing note added');
      setNursingNote('');
      await loadNursingHistory();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to add nursing note');
    } finally {
      setSaving(false);
    }
  };

  const createTask = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedPatientId || !appointmentId || !taskTitle.trim()) {
      toast.error('Patient, appointment ID and task title are required');
      return;
    }

    try {
      setSaving(true);
      await apiClient.post('/nurse/tasks/', {
        appointment: appointmentId,
        patient: selectedPatientId,
        title: taskTitle.trim(),
        details: taskDetails.trim(),
      });
      toast.success('Task created');
      setTaskTitle('');
      setTaskDetails('');
      await loadDashboard();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to create nursing task');
    } finally {
      setSaving(false);
    }
  };

  const updateTaskStatus = async (taskId: number, status: 'PENDING' | 'IN_PROGRESS' | 'DONE') => {
    try {
      await apiClient.patch('/nurse/tasks/', { id: taskId, status });
      toast.success('Task updated');
      await loadDashboard();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to update task');
    }
  };

  const updateTriagePriority = async (triageId: number, nextPriority: 'P1' | 'P2' | 'P3' | 'P4') => {
    try {
      await apiClient.patch(`/ai-triage/${triageId}/priority/`, { priority: nextPriority });
      toast.success('Triage priority updated');
      await loadDashboard();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to update triage priority');
    }
  };

  const loadNursingHistory = useCallback(async () => {
    if (!appointmentId) {
      setNotesHistory([]);
      return;
    }

    try {
      const response = await apiClient.get<{ results: NursingNoteItem[] }>(`/nurse/notes/?appointment_id=${appointmentId}`);
      setNotesHistory(response.results || []);
    } catch {
      setNotesHistory([]);
    }
  }, [appointmentId]);

  useEffect(() => {
    void loadNursingHistory();
  }, [loadNursingHistory]);

  const refreshPatientSafetySnapshot = async () => {
    if (!selectedPatientId) {
      return;
    }

    try {
      setPatientSafetyLoading(true);
      setPatientSafetyError(null);
      const [profileRes, allergyRes, vitalsRes] = await Promise.all([
        apiClient.get<PatientProfile>(`/patients/${selectedPatientId}/`),
        apiClient.get<{ count: number; results: AllergyItem[] }>(`/patients/${selectedPatientId}/allergies/`),
        apiClient.get<{ count: number; results: VitalLogItem[] }>(`/vital-logs/?patient=${selectedPatientId}&page_size=5`),
      ]);

      setSelectedPatientProfile(profileRes);
      setPatientAllergies(allergyRes.results || []);
      setPatientVitals(vitalsRes.results || []);
    } catch (err: any) {
      setPatientSafetyError(err?.message || 'Failed to refresh patient safety snapshot');
    } finally {
      setPatientSafetyLoading(false);
    }
  };

  if (authLoading) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <p className="text-sm text-gray-500">Loading nurse workspace...</p>
        </div>
      </MainLayout>
    );
  }

  if (!canAccess) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <p className="text-sm text-gray-500">Nurse workflow is available for nurse/admin/doctor roles.</p>
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
        <PageHeader
          title="Nurse Workflow Dashboard"
          description="Capture vitals, update triage severity, and handoff to doctor with nursing notes."
          actions={
            <button onClick={loadDashboard} className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
              Refresh
            </button>
          }
        />

        <div className="grid gap-4 md:grid-cols-4">
          <StatCard label="Active Queue" value={kpis.active_queue_count} tone="blue" />
          <StatCard label="P1/P2 Triage" value={kpis.high_priority_triage_count} tone="red" />
          <StatCard label="Pending Tasks" value={kpis.pending_tasks_count} tone="amber" />
          <StatCard label="Today Appointments" value={kpis.today_appointments_count} tone="slate" />
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <section className="space-y-3 rounded-lg border border-gray-200 bg-white p-5 shadow-sm xl:col-span-1">
            <h2 className="text-lg font-semibold text-gray-900">Patient Context</h2>
            <div className="flex gap-2">
              <input value={patientQuery} onChange={(e) => setPatientQuery(e.target.value)} placeholder="Search patient" className="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
              <button onClick={searchPatients} className="rounded bg-slate-800 px-3 py-2 text-sm text-white hover:bg-black">Find</button>
            </div>
            {patientOptions.length > 0 && (
              <div className="max-h-36 overflow-auto rounded border border-gray-200">
                {patientOptions.map((p) => (
                  <button key={p.id} type="button" onClick={() => setSelectedPatientId(p.id)} className={`block w-full px-3 py-2 text-left text-sm ${selectedPatientId === p.id ? 'bg-blue-50 text-blue-700' : 'hover:bg-gray-50 text-gray-700'}`}>
                    {p.full_name} <span className="text-xs text-gray-500">({p.user.email})</span>
                  </button>
                ))}
              </div>
            )}
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Appointment ID</label>
              <input
                type="number"
                value={appointmentId || ''}
                onChange={(e) => setAppointmentId(e.target.value ? Number(e.target.value) : null)}
                className="w-full rounded border border-gray-300 px-3 py-2 text-sm"
                placeholder="Enter appointment ID"
              />
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-semibold text-slate-900">Safety Snapshot</h3>
                <button
                  type="button"
                  onClick={refreshPatientSafetySnapshot}
                  disabled={!selectedPatientId || patientSafetyLoading}
                  className="text-xs font-medium text-blue-700 hover:text-blue-900 disabled:text-gray-400"
                >
                  Refresh
                </button>
              </div>

              {!selectedPatientId ? (
                <p className="mt-2 text-xs text-slate-600">Select a patient to review allergies and recent vitals.</p>
              ) : patientSafetyLoading ? (
                <p className="mt-2 text-xs text-slate-600">Loading safety data...</p>
              ) : patientSafetyError ? (
                <p className="mt-2 text-xs text-red-700">{patientSafetyError}</p>
              ) : selectedPatientProfile ? (
                <div className="mt-2 space-y-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{selectedPatientProfile.full_name || `Patient #${selectedPatientProfile.id}`}</p>
                    <p className="text-xs text-slate-600">{selectedPatientProfile.user.email} {selectedPatientProfile.blood_group ? `• ${selectedPatientProfile.blood_group}` : ''}</p>
                  </div>

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Allergies</p>
                    {patientAllergies.length === 0 ? (
                      <p className="mt-1 text-xs text-green-700">No allergies on file.</p>
                    ) : (
                      <div className="mt-2 space-y-2">
                        {patientAllergies.map((allergy) => (
                          <div key={allergy.id} className="rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                            <p className="font-semibold">{allergy.allergen} <span className="font-normal">({allergy.severity})</span></p>
                            <p>{allergy.reaction || 'Reaction not specified'}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recent Vitals</p>
                    {patientVitals.length === 0 ? (
                      <p className="mt-1 text-xs text-slate-600">No recent vitals logged.</p>
                    ) : (
                      <div className="mt-2 space-y-2">
                        {patientVitals.map((vital) => (
                          <div key={vital.id} className="rounded border border-slate-200 bg-white px-3 py-2 text-xs text-slate-700">
                            <p className="font-semibold text-slate-900">{new Date(vital.recorded_at).toLocaleString()}</p>
                            <p>BP {vital.blood_pressure || 'N/A'} | Pulse {vital.pulse ?? 'N/A'} | Temp {vital.temperature_c ?? 'N/A'} C</p>
                            <p>RR {vital.respiratory_rate ?? 'N/A'} | SpO2 {vital.oxygen_saturation ?? 'N/A'}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          </section>

          <section className="space-y-3 rounded-lg border border-gray-200 bg-white p-5 shadow-sm xl:col-span-2">
            <h2 className="text-lg font-semibold text-gray-900">Capture Vitals</h2>
            <form onSubmit={createVitalLog} className="grid gap-3 md:grid-cols-2">
              <input value={bp} onChange={(e) => setBp(e.target.value)} placeholder="BP (e.g. 120/80)" className="rounded border border-gray-300 px-3 py-2 text-sm" />
              <input value={pulse} onChange={(e) => setPulse(e.target.value)} placeholder="Pulse" className="rounded border border-gray-300 px-3 py-2 text-sm" />
              <input value={temp} onChange={(e) => setTemp(e.target.value)} placeholder="Temperature C" className="rounded border border-gray-300 px-3 py-2 text-sm" />
              <input value={respRate} onChange={(e) => setRespRate(e.target.value)} placeholder="Respiratory rate" className="rounded border border-gray-300 px-3 py-2 text-sm" />
              <input value={spo2} onChange={(e) => setSpo2(e.target.value)} placeholder="SpO2" className="rounded border border-gray-300 px-3 py-2 text-sm" />
              <textarea value={vitalsNotes} onChange={(e) => setVitalsNotes(e.target.value)} placeholder="Vitals notes" className="rounded border border-gray-300 px-3 py-2 text-sm md:col-span-2" rows={2} />
              <button disabled={saving || !selectedPatientId} className="rounded bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400 md:col-span-2">
                Save Vitals
              </button>
            </form>
          </section>
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          <SectionCard title="Nursing Notes (Doctor Handoff)">
            <form onSubmit={createNurseNote} className="space-y-3">
              <select value={triageTag} onChange={(e) => setTriageTag(e.target.value as 'P1' | 'P2' | 'P3' | 'P4')} className="w-full rounded border border-gray-300 px-3 py-2 text-sm">
                <option value="P1">P1</option>
                <option value="P2">P2</option>
                <option value="P3">P3</option>
                <option value="P4">P4</option>
              </select>
              <textarea value={nursingNote} onChange={(e) => setNursingNote(e.target.value)} rows={3} className="w-full rounded border border-gray-300 px-3 py-2 text-sm" placeholder="Clinical handoff note for doctor" />
              <button disabled={saving || !selectedPatientId || !appointmentId} className="rounded bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:bg-gray-400">
                Add Nursing Note
              </button>
            </form>

            <div className="space-y-2">
              {notesHistory.length === 0 ? (
                <EmptyState title="No handoff notes" description="Nursing notes for the selected appointment will appear here." />
              ) : (
                notesHistory.map((item) => (
                  <div key={item.id} className="rounded border border-gray-200 p-3">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <StatusBadge value={item.triage_tag} />
                      <span>{item.nurse_name || 'Nurse'} • {new Date(item.created_at).toLocaleString()}</span>
                    </div>
                    <p className="mt-1 text-sm text-gray-700">{item.note}</p>
                  </div>
                ))
              )}
            </div>
          </SectionCard>

          <SectionCard title="Nursing Tasks Checklist">
            <form onSubmit={createTask} className="space-y-3">
              <input value={taskTitle} onChange={(e) => setTaskTitle(e.target.value)} placeholder="Task title" className="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
              <textarea value={taskDetails} onChange={(e) => setTaskDetails(e.target.value)} rows={2} placeholder="Task details" className="w-full rounded border border-gray-300 px-3 py-2 text-sm" />
              <button disabled={saving || !selectedPatientId || !appointmentId} className="rounded bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-gray-400">
                Create Task
              </button>
            </form>

            <div className="space-y-2">
              {taskItems.length === 0 ? (
                <EmptyState title="No pending tasks" description="Tasks assigned for this role and appointment will appear here." />
              ) : (
                taskItems.map((task) => (
                  <div key={task.id} className="rounded border border-gray-200 p-3">
                    <p className="text-sm font-semibold text-gray-900">{task.title}</p>
                    <p className="text-xs text-gray-500">{task.patient_name} • Appt #{task.appointment}</p>
                    <p className="mt-1 text-sm text-gray-700">{task.details || 'No details'}</p>
                    <div className="mt-2">
                      <StatusBadge value={task.status} />
                    </div>
                    <div className="mt-2 flex gap-2">
                      <button onClick={() => updateTaskStatus(task.id, 'IN_PROGRESS')} className="rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-700">In Progress</button>
                      <button onClick={() => updateTaskStatus(task.id, 'DONE')} className="rounded border border-green-300 bg-green-50 px-2 py-1 text-xs text-green-700">Done</button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </SectionCard>
        </div>

        <SectionCard title="Queue and Triage Severity" subtitle="Live queue status and triage urgency controls.">
          {loading ? (
            <p className="text-sm text-gray-600">Loading...</p>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <h3 className="mb-2 text-sm font-semibold text-gray-700">Active Queue</h3>
                <div className="space-y-2">
                  {queueItems.slice(0, 20).length === 0 ? (
                    <EmptyState title="Queue is clear" description="No active queue entries right now." />
                  ) : (
                    queueItems.slice(0, 20).map((item) => (
                      <div key={item.id} className="rounded border border-gray-200 p-2 text-sm">
                        <p className="font-medium text-gray-900">{item.patient_name}</p>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                          <span>{item.doctor_name} • wait {item.wait_time_minutes}m</span>
                          <StatusBadge value={item.status} />
                          <StatusBadge value={item.priority} />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-gray-700">Recent Triage</h3>
                <div className="space-y-2">
                  {triageItems.slice(0, 20).length === 0 ? (
                    <EmptyState title="No recent triage entries" description="New triage assessments will show up here." />
                  ) : (
                    triageItems.slice(0, 20).map((item) => (
                      <div key={item.id} className="rounded border border-gray-200 p-2 text-sm">
                        <p className="font-medium text-gray-900">{item.patient_name}</p>
                        <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                          <StatusBadge value={item.priority} />
                          <span>{new Date(item.created_at).toLocaleString()}</span>
                        </div>
                        <p className="mt-1 text-xs text-gray-600">{item.symptoms}</p>
                        <div className="mt-2 flex gap-1">
                          {(['P1', 'P2', 'P3', 'P4'] as const).map((p) => (
                            <button
                              key={p}
                              onClick={() => updateTriagePriority(item.id, p)}
                              className={`rounded px-2 py-1 text-xs ${item.priority === p ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
                            >
                              {p}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </SectionCard>
      </div>
    </MainLayout>
  );
}
