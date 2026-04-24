'use client';

import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';

interface EmergencyEncounter {
  id: number;
  patient: number;
  patient_name: string;
  assigned_doctor: number | null;
  doctor_name?: string | null;
  arrival_mode: 'WALK_IN' | 'AMBULANCE' | 'REFERRAL' | 'POLICE' | 'OTHER';
  triage_level: 'ESI_1' | 'ESI_2' | 'ESI_3' | 'ESI_4' | 'ESI_5' | '';
  severity_priority: number;
  status: 'REGISTERED' | 'TRIAGED' | 'IN_TREATMENT' | 'ADMITTED' | 'TRANSFERRED' | 'DISCHARGED' | 'DECEASED';
  chief_complaint: string;
  arrived_at: string;
}

interface PatientOption {
  id: number;
  full_name: string;
}

interface EmergencyFormState {
  patient: string;
  chief_complaint: string;
  arrival_mode: 'WALK_IN' | 'AMBULANCE' | 'REFERRAL' | 'POLICE' | 'OTHER';
  severity_priority: string;
  triage_level: 'ESI_1' | 'ESI_2' | 'ESI_3' | 'ESI_4' | 'ESI_5';
}

const initialForm: EmergencyFormState = {
  patient: '',
  chief_complaint: '',
  arrival_mode: 'WALK_IN',
  severity_priority: '3',
  triage_level: 'ESI_3',
};

export default function EmergencyPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [encounters, setEncounters] = useState<EmergencyEncounter[]>([]);
  const [patientQuery, setPatientQuery] = useState('');
  const [patientOptions, setPatientOptions] = useState<PatientOption[]>([]);
  const [form, setForm] = useState({ ...initialForm });

  const { userRole } = useAuth();
  const canAccess = useMemo(
    () => ACCESS_MATRIX.emergency.includes((userRole || '').toUpperCase() as (typeof ACCESS_MATRIX.emergency)[number]),
    [userRole]
  );

  const summary = useMemo(() => {
    return {
      active: encounters.filter((item) => ['REGISTERED', 'TRIAGED', 'IN_TREATMENT'].includes(item.status)).length,
      critical: encounters.filter((item) => item.severity_priority <= 2).length,
      discharged: encounters.filter((item) => item.status === 'DISCHARGED').length,
    };
  }, [encounters]);

  const loadEncounters = async () => {
    try {
      setIsLoading(true);
      const [queue, all] = await Promise.all([
        apiClient.get<EmergencyEncounter[]>('/emergency/triage-queue/'),
        apiClient.get<EmergencyEncounter[]>('/emergency/encounters/'),
      ]);

      const merged = [...queue, ...all].reduce<EmergencyEncounter[]>((acc, curr) => {
        if (!acc.find((item) => item.id === curr.id)) {
          acc.push(curr);
        }
        return acc;
      }, []);

      merged.sort((a, b) => {
        if (a.severity_priority !== b.severity_priority) return a.severity_priority - b.severity_priority;
        return new Date(b.arrived_at).getTime() - new Date(a.arrived_at).getTime();
      });

      setEncounters(merged);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to load emergency encounters');
    } finally {
      setIsLoading(false);
    }
  };

  const searchPatients = async (query: string) => {
    if (!query.trim()) {
      setPatientOptions([]);
      return;
    }
    try {
      const data = await apiClient.get<{ results: PatientOption[] }>(`/patients/?q=${encodeURIComponent(query)}&page_size=8`);
      setPatientOptions(data.results || []);
    } catch {
      setPatientOptions([]);
    }
  };

  useEffect(() => {
    if (!canAccess) return;
    loadEncounters();
  }, [canAccess]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      searchPatients(patientQuery);
    }, 250);
    return () => clearTimeout(timeout);
  }, [patientQuery]);

  const onCreateEncounter = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.patient || !form.chief_complaint.trim()) {
      toast.error('Patient and chief complaint are required');
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.post('/emergency/encounters/', {
        patient: Number(form.patient),
        chief_complaint: form.chief_complaint.trim(),
        arrival_mode: form.arrival_mode,
        severity_priority: Number(form.severity_priority),
        triage_level: form.triage_level,
      });
      toast.success('Emergency encounter registered');
      setForm({ ...initialForm });
      setPatientQuery('');
      setPatientOptions([]);
      await loadEncounters();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to register emergency encounter');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.emergency}
      title="emergency department"
      description="Emergency workflow is restricted to emergency-facing clinical and operations roles."
    >
      <div className="space-y-6">
        <PageHeader
          title="Emergency Department"
          description="Register, triage, and monitor emergency encounters in real-time."
        />

        <div className="grid gap-4 md:grid-cols-3">
          <StatCard label="Active ED Cases" value={summary.active} tone="amber" />
          <StatCard label="High Severity (P1-P2)" value={summary.critical} tone="red" />
          <StatCard label="Discharged" value={summary.discharged} tone="green" />
        </div>

        <SectionCard title="Register Emergency Encounter" subtitle="Capture arrival and initial triage details.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={onCreateEncounter}>
            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">Search patient</label>
              <input
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={patientQuery}
                onChange={(e) => {
                  setPatientQuery(e.target.value);
                  setForm((prev) => ({ ...prev, patient: '' }));
                }}
                placeholder="Type patient name"
              />
              {patientOptions.length > 0 && (
                <div className="mt-2 max-h-40 overflow-auto rounded-lg border border-gray-200 bg-white">
                  {patientOptions.map((patient) => (
                    <button
                      type="button"
                      key={patient.id}
                      className="block w-full border-b border-gray-100 px-3 py-2 text-left text-sm hover:bg-gray-50"
                      onClick={() => {
                        setForm((prev) => ({ ...prev, patient: String(patient.id) }));
                        setPatientQuery(patient.full_name);
                        setPatientOptions([]);
                      }}
                    >
                      {patient.full_name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Arrival mode</label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={form.arrival_mode}
                onChange={(e) => setForm((prev) => ({ ...prev, arrival_mode: e.target.value as typeof prev.arrival_mode }))}
              >
                <option value="WALK_IN">Walk-in</option>
                <option value="AMBULANCE">Ambulance</option>
                <option value="REFERRAL">Referral</option>
                <option value="POLICE">Police</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Severity priority</label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={form.severity_priority}
                onChange={(e) => setForm((prev) => ({ ...prev, severity_priority: e.target.value }))}
              >
                <option value="1">P1</option>
                <option value="2">P2</option>
                <option value="3">P3</option>
                <option value="4">P4</option>
                <option value="5">P5</option>
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Triage level</label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={form.triage_level}
                onChange={(e) => setForm((prev) => ({ ...prev, triage_level: e.target.value as typeof prev.triage_level }))}
              >
                <option value="ESI_1">ESI 1</option>
                <option value="ESI_2">ESI 2</option>
                <option value="ESI_3">ESI 3</option>
                <option value="ESI_4">ESI 4</option>
                <option value="ESI_5">ESI 5</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">Chief complaint</label>
              <textarea
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                rows={3}
                value={form.chief_complaint}
                onChange={(e) => setForm((prev) => ({ ...prev, chief_complaint: e.target.value }))}
                placeholder="Reason for emergency visit"
              />
            </div>

            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={isSaving}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
              >
                {isSaving ? 'Registering...' : 'Register Encounter'}
              </button>
            </div>
          </form>
        </SectionCard>

        <SectionCard title="Emergency Queue" subtitle="Priority-sorted list of emergency cases.">
          {isLoading ? (
            <div className="p-6 text-center text-gray-500">Loading emergency queue...</div>
          ) : encounters.length === 0 ? (
            <EmptyState title="No emergency cases" description="New emergency registrations will appear here." />
          ) : (
            <div className="divide-y divide-gray-100">
              {encounters.map((encounter) => (
                <div key={encounter.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-gray-900">ED-{encounter.id} {encounter.patient_name}</p>
                      <StatusBadge value={encounter.status} />
                    </div>
                    <p className="text-sm text-gray-600">{encounter.chief_complaint}</p>
                    <p className="text-xs text-gray-500">
                      {encounter.arrival_mode} | {encounter.triage_level || 'No ESI'} | Priority P{encounter.severity_priority}
                    </p>
                  </div>
                  <Link
                    href={`/emergency/encounters/${encounter.id}`}
                    className="rounded-md bg-slate-700 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800"
                  >
                    Open Case
                  </Link>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </ProtectedPage>
  );
}
