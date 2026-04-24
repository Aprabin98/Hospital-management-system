'use client';

import React, { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useRoleAccess } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';
import { EmptyState, PageHeader, SectionCard, StatusBadge } from '@/components/UI';

interface EmergencyEncounter {
  id: number;
  patient: number;
  patient_name: string;
  assigned_doctor: number | null;
  doctor_name?: string | null;
  arrival_mode: string;
  triage_level: string;
  severity_priority: number;
  status: string;
  chief_complaint: string;
  stabilization_notes: string;
  disposition_notes: string;
  arrived_at: string;
}

interface InpatientStay {
  id: number;
  patient: number;
  status: 'ADMITTED' | 'DISCHARGED' | 'TRANSFERRED';
}

interface TriageRecord {
  id: number;
  pulse: number | null;
  systolic_bp: number | null;
  diastolic_bp: number | null;
  temperature_c: number | null;
  respiratory_rate: number | null;
  oxygen_saturation: number | null;
  pain_score: number;
  triage_notes: string;
  created_at: string;
}

interface ClinicalNote {
  id: number;
  note_type: 'NURSING' | 'DOCTOR' | 'STABILIZATION' | 'GENERAL';
  content: string;
  author_name?: string | null;
  created_at: string;
}

export default function EmergencyEncounterDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const encounterId = Number(params?.id);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [encounter, setEncounter] = useState<EmergencyEncounter | null>(null);
  const [triageRecords, setTriageRecords] = useState<TriageRecord[]>([]);
  const [notes, setNotes] = useState<ClinicalNote[]>([]);

  const [status, setStatus] = useState('IN_TREATMENT');
  const [isDispositionLoading, setIsDispositionLoading] = useState(false);
  const [triageForm, setTriageForm] = useState({
    pulse: '',
    systolic_bp: '',
    diastolic_bp: '',
    temperature_c: '',
    respiratory_rate: '',
    oxygen_saturation: '',
    pain_score: '4',
    triage_notes: '',
  });
  const [noteType, setNoteType] = useState<ClinicalNote['note_type']>('GENERAL');
  const [noteContent, setNoteContent] = useState('');

  const { canAccess } = useRoleAccess(ACCESS_MATRIX.emergency);

  const loadData = useCallback(async () => {
    if (!encounterId) return;
    try {
      setIsLoading(true);
      const [encounterData, triageData, notesData] = await Promise.all([
        apiClient.get<EmergencyEncounter>(`/emergency/encounters/${encounterId}/`),
        apiClient.get<TriageRecord[]>(`/emergency/encounters/${encounterId}/triage/`),
        apiClient.get<ClinicalNote[]>(`/emergency/encounters/${encounterId}/notes/`),
      ]);
      setEncounter(encounterData);
      setStatus(encounterData.status || 'IN_TREATMENT');
      setTriageRecords(triageData || []);
      setNotes(notesData || []);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to load emergency case');
    } finally {
      setIsLoading(false);
    }
  }, [encounterId]);

  useEffect(() => {
    if (!canAccess || !encounterId) return;
    void loadData();
  }, [canAccess, encounterId, loadData]);

  const updateStatus = async () => {
    try {
      setIsSaving(true);
      await apiClient.patch(`/emergency/encounters/${encounterId}/`, { status });
      toast.success('Emergency status updated');
      await loadData();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update status');
    } finally {
      setIsSaving(false);
    }
  };

  const findLatestAdmittedStay = async (patientId: number) => {
    const response = await apiClient.get<{ count: number; results: InpatientStay[] }>('/ipd/stays/?active=true');
    const matching = (response.results || []).filter((stay) => stay.patient === patientId);
    if (matching.length === 0) {
      return null;
    }
    return matching.sort((a, b) => b.id - a.id)[0];
  };

  const createIpdStayFromEncounter = async () => {
    if (!encounter) {
      throw new Error('Emergency encounter data not loaded');
    }

    return apiClient.post<InpatientStay>('/ipd/stays/', {
      patient_id: encounter.patient,
      attending_doctor_id: encounter.assigned_doctor,
      primary_diagnosis: encounter.chief_complaint,
      admission_reason: `Admitted from ED case ED-${encounter.id}`,
    });
  };

  const handleAdmitToIpd = async () => {
    try {
      setIsDispositionLoading(true);
      const stay = await createIpdStayFromEncounter();
      await apiClient.patch(`/emergency/encounters/${encounterId}/`, { status: 'ADMITTED' });
      toast.success('Patient admitted to IPD from emergency');
      router.push(`/ipd/stays/${stay.id}`);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to admit patient to IPD');
    } finally {
      setIsDispositionLoading(false);
    }
  };

  const handleTransferToIpd = async () => {
    try {
      setIsDispositionLoading(true);
      if (!encounter) {
        throw new Error('Emergency encounter data not loaded');
      }

      let stay = await findLatestAdmittedStay(encounter.patient);
      if (!stay) {
        stay = await createIpdStayFromEncounter();
      }

      await apiClient.patch(`/ipd/stays/${stay.id}/`, {
        status: 'TRANSFERRED',
        care_notes: `Transferred from ED case ED-${encounter.id}`,
      });
      await apiClient.patch(`/emergency/encounters/${encounterId}/`, { status: 'TRANSFERRED' });
      toast.success('Patient transfer to IPD recorded');
      router.push(`/ipd/stays/${stay.id}`);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to transfer patient through IPD flow');
    } finally {
      setIsDispositionLoading(false);
    }
  };

  const handleDischargeViaIpd = async () => {
    try {
      setIsDispositionLoading(true);
      if (!encounter) {
        throw new Error('Emergency encounter data not loaded');
      }

      const stay = await findLatestAdmittedStay(encounter.patient);
      if (!stay) {
        throw new Error('No active IPD stay found for this patient');
      }

      await apiClient.patch(`/ipd/stays/${stay.id}/`, {
        status: 'DISCHARGED',
        care_notes: `Discharged via ED workflow for case ED-${encounter.id}`,
      });
      await apiClient.patch(`/emergency/encounters/${encounterId}/`, { status: 'DISCHARGED' });
      toast.success('Patient discharged through IPD flow');
      await loadData();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to discharge patient through IPD flow');
    } finally {
      setIsDispositionLoading(false);
    }
  };

  const submitTriage = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      await apiClient.post(`/emergency/encounters/${encounterId}/triage/`, {
        pulse: triageForm.pulse ? Number(triageForm.pulse) : null,
        systolic_bp: triageForm.systolic_bp ? Number(triageForm.systolic_bp) : null,
        diastolic_bp: triageForm.diastolic_bp ? Number(triageForm.diastolic_bp) : null,
        temperature_c: triageForm.temperature_c ? Number(triageForm.temperature_c) : null,
        respiratory_rate: triageForm.respiratory_rate ? Number(triageForm.respiratory_rate) : null,
        oxygen_saturation: triageForm.oxygen_saturation ? Number(triageForm.oxygen_saturation) : null,
        pain_score: Number(triageForm.pain_score),
        triage_notes: triageForm.triage_notes,
      });
      toast.success('Triage record added');
      setTriageForm({
        pulse: '',
        systolic_bp: '',
        diastolic_bp: '',
        temperature_c: '',
        respiratory_rate: '',
        oxygen_saturation: '',
        pain_score: '4',
        triage_notes: '',
      });
      await loadData();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to add triage record');
    } finally {
      setIsSaving(false);
    }
  };

  const submitNote = async (e: FormEvent) => {
    e.preventDefault();
    if (!noteContent.trim()) {
      toast.error('Clinical note cannot be empty');
      return;
    }
    try {
      setIsSaving(true);
      await apiClient.post(`/emergency/encounters/${encounterId}/notes/`, {
        note_type: noteType,
        content: noteContent.trim(),
      });
      toast.success('Clinical note added');
      setNoteContent('');
      await loadData();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to add note');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.emergency}
      title="emergency case"
      description="Emergency case access is restricted to emergency-facing clinical and operations roles."
    >
      <div className="space-y-6">
        <PageHeader
          title={encounter ? `Emergency Case ED-${encounter.id}` : 'Emergency Case'}
          description={encounter?.chief_complaint || 'Track triage, notes, and disposition actions.'}
          actions={
            <Link href="/emergency" className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
              Back to Emergency
            </Link>
          }
        />

        {isLoading ? (
          <SectionCard title="Loading" subtitle="Fetching emergency case details...">
            <div className="p-6 text-sm text-gray-500">Please wait...</div>
          </SectionCard>
        ) : !encounter ? (
          <EmptyState title="Case not found" description="The emergency encounter could not be loaded." />
        ) : (
          <>
            <SectionCard title="Case Status" subtitle="Update disposition as treatment progresses.">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge value={encounter.status} />
                <select
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="REGISTERED">Registered</option>
                  <option value="TRIAGED">Triaged</option>
                  <option value="IN_TREATMENT">In Treatment</option>
                  <option value="ADMITTED">Admitted</option>
                  <option value="TRANSFERRED">Transferred</option>
                  <option value="DISCHARGED">Discharged</option>
                  <option value="DECEASED">Deceased</option>
                </select>
                <button
                  type="button"
                  onClick={updateStatus}
                  disabled={isSaving}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
                >
                  Update Status
                </button>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleAdmitToIpd}
                  disabled={isDispositionLoading}
                  className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
                >
                  Admit To IPD
                </button>
                <button
                  type="button"
                  onClick={handleTransferToIpd}
                  disabled={isDispositionLoading}
                  className="rounded-lg bg-amber-600 px-3 py-2 text-xs font-semibold text-white hover:bg-amber-700 disabled:opacity-60"
                >
                  Transfer Via IPD
                </button>
                <button
                  type="button"
                  onClick={handleDischargeViaIpd}
                  disabled={isDispositionLoading}
                  className="rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-60"
                >
                  Discharge Via IPD
                </button>
              </div>
              <p className="mt-3 text-xs text-gray-500">
                Arrival: {encounter.arrival_mode} | Triage: {encounter.triage_level || 'Not set'} | Priority: P{encounter.severity_priority}
              </p>
            </SectionCard>

            <div className="grid gap-6 lg:grid-cols-2">
              <SectionCard title="Add Triage Record" subtitle="Capture latest emergency vitals and triage notes.">
                <form className="grid gap-3 md:grid-cols-2" onSubmit={submitTriage}>
                  <input className="rounded-lg border border-gray-300 px-3 py-2 text-sm" placeholder="Pulse" value={triageForm.pulse} onChange={(e) => setTriageForm((prev) => ({ ...prev, pulse: e.target.value }))} />
                  <input className="rounded-lg border border-gray-300 px-3 py-2 text-sm" placeholder="Systolic BP" value={triageForm.systolic_bp} onChange={(e) => setTriageForm((prev) => ({ ...prev, systolic_bp: e.target.value }))} />
                  <input className="rounded-lg border border-gray-300 px-3 py-2 text-sm" placeholder="Diastolic BP" value={triageForm.diastolic_bp} onChange={(e) => setTriageForm((prev) => ({ ...prev, diastolic_bp: e.target.value }))} />
                  <input className="rounded-lg border border-gray-300 px-3 py-2 text-sm" placeholder="Temp (C)" value={triageForm.temperature_c} onChange={(e) => setTriageForm((prev) => ({ ...prev, temperature_c: e.target.value }))} />
                  <input className="rounded-lg border border-gray-300 px-3 py-2 text-sm" placeholder="Respiratory Rate" value={triageForm.respiratory_rate} onChange={(e) => setTriageForm((prev) => ({ ...prev, respiratory_rate: e.target.value }))} />
                  <input className="rounded-lg border border-gray-300 px-3 py-2 text-sm" placeholder="SpO2" value={triageForm.oxygen_saturation} onChange={(e) => setTriageForm((prev) => ({ ...prev, oxygen_saturation: e.target.value }))} />
                  <div className="md:col-span-2">
                    <label className="mb-1 block text-sm font-medium text-gray-700">Pain score</label>
                    <select className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" value={triageForm.pain_score} onChange={(e) => setTriageForm((prev) => ({ ...prev, pain_score: e.target.value }))}>
                      {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((score) => (
                        <option key={score} value={String(score)}>{score}</option>
                      ))}
                    </select>
                  </div>
                  <textarea className="md:col-span-2 rounded-lg border border-gray-300 px-3 py-2 text-sm" rows={3} placeholder="Triage notes" value={triageForm.triage_notes} onChange={(e) => setTriageForm((prev) => ({ ...prev, triage_notes: e.target.value }))} />
                  <button type="submit" disabled={isSaving} className="md:col-span-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
                    Add Triage Record
                  </button>
                </form>
              </SectionCard>

              <SectionCard title="Add Clinical Note" subtitle="Track doctor/nursing/stabilization notes.">
                <form className="space-y-3" onSubmit={submitNote}>
                  <select className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" value={noteType} onChange={(e) => setNoteType(e.target.value as ClinicalNote['note_type'])}>
                    <option value="GENERAL">General</option>
                    <option value="NURSING">Nursing</option>
                    <option value="DOCTOR">Doctor</option>
                    <option value="STABILIZATION">Stabilization</option>
                  </select>
                  <textarea className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm" rows={5} placeholder="Write clinical note" value={noteContent} onChange={(e) => setNoteContent(e.target.value)} />
                  <button type="submit" disabled={isSaving} className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60">
                    Save Note
                  </button>
                </form>
              </SectionCard>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <SectionCard title="Triage History" subtitle="Latest triage observations for this encounter.">
                {triageRecords.length === 0 ? (
                  <EmptyState title="No triage records" description="Add first triage assessment from the form above." />
                ) : (
                  <div className="space-y-3">
                    {triageRecords.map((record) => (
                      <div key={record.id} className="rounded-lg border border-gray-200 p-3 text-sm">
                        <p className="font-semibold text-gray-900">Pain {record.pain_score} | SpO2 {record.oxygen_saturation ?? '-'}%</p>
                        <p className="text-gray-600">
                          Pulse {record.pulse ?? '-'} | BP {record.systolic_bp ?? '-'} / {record.diastolic_bp ?? '-'} | Temp {record.temperature_c ?? '-'} C
                        </p>
                        {record.triage_notes && <p className="mt-1 text-gray-700">{record.triage_notes}</p>}
                        <p className="mt-1 text-xs text-gray-500">{new Date(record.created_at).toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>

              <SectionCard title="Clinical Notes" subtitle="Chronological notes for ED care decisions.">
                {notes.length === 0 ? (
                  <EmptyState title="No notes yet" description="Add nursing/doctor/stabilization notes." />
                ) : (
                  <div className="space-y-3">
                    {notes.map((item) => (
                      <div key={item.id} className="rounded-lg border border-gray-200 p-3 text-sm">
                        <div className="mb-1 flex items-center justify-between">
                          <StatusBadge value={item.note_type} />
                          <span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-gray-800">{item.content}</p>
                        <p className="mt-1 text-xs text-gray-500">{item.author_name || 'Unknown author'}</p>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>
          </>
        )}
      </div>
    </ProtectedPage>
  );
}
