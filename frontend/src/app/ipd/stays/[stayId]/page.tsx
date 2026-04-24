'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useRoleAccess } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface StayPayload {
  stay: {
    id: number;
    patient_name: string;
    primary_diagnosis: string;
    admission_reason: string;
    status: string;
    bed_label: string;
    attending_doctor_name: string;
    expected_discharge_date: string | null;
    length_of_stay_days: number;
  };
}

interface ProgressNote {
  id: number;
  note_type: string;
  author_name: string;
  clinical_findings: string;
  assessment: string;
  plan: string;
  created_at: string;
}

interface DailyRound {
  id: number;
  round_date: string;
  round_assessor_name: string;
  round_notes: string;
  current_status: string;
  orders: string;
  is_signed: boolean;
}

interface MarEntry {
  id: number;
  medication_name: string;
  dose_given: string;
  route: string;
  scheduled_datetime: string;
  administered_datetime: string | null;
  status: string;
  administered_by_name: string;
  reason_not_given: string;
  deviations: string;
  notes: string;
  created_at: string;
}

interface DischargePackage {
  id: number;
  discharge_summary: string;
  discharge_diagnoses: string;
  discharge_instructions: string;
  follow_up_date: string;
  follow_up_provider: string;
  follow_up_specialty: string;
  nursing_clearance: boolean;
  pharmacy_clearance: boolean;
  billing_clearance: boolean;
  final_approved: boolean;
  checklist_complete: boolean;
  doctor_signed_off_by_name: string;
  patient_acknowledged_by_name: string;
}

export default function StayDetailPage() {
  const params = useParams<{ stayId: string }>();
  const stayId = params?.stayId;

  const [payload, setPayload] = useState<StayPayload | null>(null);
  const [progressNotes, setProgressNotes] = useState<ProgressNote[]>([]);
  const [dailyRounds, setDailyRounds] = useState<DailyRound[]>([]);
  const [marEntries, setMarEntries] = useState<MarEntry[]>([]);
  const [dischargePackage, setDischargePackage] = useState<DischargePackage | null>(null);
  const [newAssessment, setNewAssessment] = useState('');
  const [newPlan, setNewPlan] = useState('');
  const [newRoundNotes, setNewRoundNotes] = useState('');
  const [newMarMedicationName, setNewMarMedicationName] = useState('');
  const [newMarDose, setNewMarDose] = useState('');
  const [newMarRoute, setNewMarRoute] = useState('');
  const [newMarScheduledAt, setNewMarScheduledAt] = useState('');
  const [newMarAdministeredAt, setNewMarAdministeredAt] = useState('');
  const [newMarStatus, setNewMarStatus] = useState('SCHEDULED');
  const [newMarReasonNotGiven, setNewMarReasonNotGiven] = useState('');
  const [newMarDeviations, setNewMarDeviations] = useState('');
  const [newMarNotes, setNewMarNotes] = useState('');
  const [isMarSaving, setIsMarSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const { canAccess, userRole } = useRoleAccess(ACCESS_MATRIX.ipd);
  const role = (userRole || '').toUpperCase();
  const canWriteNotes = ['ADMIN', 'DOCTOR', 'NURSE'].includes(role);
  const canWriteRounds = ['ADMIN', 'DOCTOR'].includes(role);

  const loadData = useCallback(async () => {
    if (!stayId) return;
    try {
      setIsLoading(true);
      const [stayRes, notesRes, roundsRes, marRes, dischargeRes] = await Promise.all([
        apiClient.get<StayPayload>(`/ipd/stays/${stayId}/`),
        apiClient.get<{ count: number; results: ProgressNote[] }>(`/ipd/stays/${stayId}/progress-notes/`),
        apiClient.get<{ count: number; results: DailyRound[] }>(`/ipd/stays/${stayId}/rounds/`),
        apiClient.get<{ count: number; results: MarEntry[] }>(`/ipd/stays/${stayId}/mar/`).catch(() => ({ count: 0, results: [] })),
        apiClient.get<DischargePackage>(`/ipd/stays/${stayId}/discharge/`).catch(() => null),
      ]);

      setPayload(stayRes);
      setProgressNotes(notesRes.results || []);
      setDailyRounds(roundsRes.results || []);
      setMarEntries(marRes.results || []);
      setDischargePackage(dischargeRes || null);
    } catch (error) {
      toast.error('Failed to load IPD stay detail');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }, [stayId]);

  useEffect(() => {
    if (!canAccess) return;
    void loadData();
  }, [canAccess, loadData]);

  const addProgressNote = async () => {
    if (!stayId || !newAssessment.trim()) return;
    try {
      await apiClient.post(`/ipd/stays/${stayId}/progress-notes/`, {
        note_type: 'PROGRESS',
        clinical_findings: '',
        assessment: newAssessment,
        plan: newPlan,
      });
      toast.success('Progress note added');
      setNewAssessment('');
      setNewPlan('');
      await loadData();
    } catch (error) {
      toast.error('Failed to add progress note');
      console.error(error);
    }
  };

  const addRound = async () => {
    if (!stayId || !newRoundNotes.trim()) return;
    try {
      await apiClient.post(`/ipd/stays/${stayId}/rounds/`, {
        round_notes: newRoundNotes,
        is_signed: true,
      });
      toast.success('Daily round added');
      setNewRoundNotes('');
      await loadData();
    } catch (error) {
      toast.error('Failed to add round');
      console.error(error);
    }
  };

  const addMarEntry = async () => {
    if (!stayId || !newMarMedicationName.trim() || !newMarDose.trim()) {
      toast.error('Medication name and dose are required');
      return;
    }

    try {
      setIsMarSaving(true);
      await apiClient.post(`/ipd/stays/${stayId}/mar/`, {
        medication_name: newMarMedicationName,
        dose_given: newMarDose,
        route: newMarRoute,
        scheduled_datetime: newMarScheduledAt || undefined,
        administered_datetime: newMarAdministeredAt || undefined,
        status: newMarStatus,
        reason_not_given: newMarReasonNotGiven,
        deviations: newMarDeviations,
        notes: newMarNotes,
      });
      toast.success('MAR entry added');
      setNewMarMedicationName('');
      setNewMarDose('');
      setNewMarRoute('');
      setNewMarScheduledAt('');
      setNewMarAdministeredAt('');
      setNewMarStatus('SCHEDULED');
      setNewMarReasonNotGiven('');
      setNewMarDeviations('');
      setNewMarNotes('');
      await loadData();
    } catch (error) {
      toast.error('Failed to add MAR entry');
      console.error(error);
    } finally {
      setIsMarSaving(false);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.ipd}
      title="inpatient stay"
      description="Inpatient stay access is restricted to IPD-authorized roles."
    >
      <div className="space-y-6">
        {isLoading ? (
          <div className="py-10 text-center text-gray-500">Loading stay details...</div>
        ) : payload?.stay ? (
          <>
            <div className="rounded-lg border border-gray-200 bg-white p-5">
              <h1 className="text-2xl font-bold text-gray-900">IPD Stay #{payload.stay.id}</h1>
              <p className="mt-1 text-gray-700">{payload.stay.patient_name}</p>
              <p className="text-sm text-gray-600">Diagnosis: {payload.stay.primary_diagnosis}</p>
              <p className="text-sm text-gray-600">Status: {payload.stay.status} | Bed: {payload.stay.bed_label || 'N/A'} | LOS: {payload.stay.length_of_stay_days} day(s)</p>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-lg border border-gray-200 bg-white p-5">
                <h2 className="mb-3 text-lg font-semibold text-gray-900">Progress Notes</h2>
                {canWriteNotes && (
                  <div className="mb-4 space-y-2">
                    <textarea
                      value={newAssessment}
                      onChange={(e) => setNewAssessment(e.target.value)}
                      placeholder="Assessment"
                      rows={2}
                      className="w-full rounded-md border border-gray-300 px-3 py-2"
                    />
                    <textarea
                      value={newPlan}
                      onChange={(e) => setNewPlan(e.target.value)}
                      placeholder="Plan"
                      rows={2}
                      className="w-full rounded-md border border-gray-300 px-3 py-2"
                    />
                    <button onClick={addProgressNote} className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700">
                      Add Note
                    </button>
                  </div>
                )}

                <div className="space-y-3">
                  {progressNotes.map((note) => (
                    <div key={note.id} className="rounded-md border border-gray-200 p-3">
                      <p className="text-xs text-gray-500">{new Date(note.created_at).toLocaleString()} - {note.author_name}</p>
                      <p className="mt-1 text-sm text-gray-800">{note.assessment}</p>
                      {note.plan && <p className="text-sm text-gray-600">Plan: {note.plan}</p>}
                    </div>
                  ))}
                  {progressNotes.length === 0 && <p className="text-sm text-gray-500">No progress notes yet.</p>}
                </div>
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-5">
                <h2 className="mb-3 text-lg font-semibold text-gray-900">Daily Rounds</h2>
                {canWriteRounds && (
                  <div className="mb-4 space-y-2">
                    <textarea
                      value={newRoundNotes}
                      onChange={(e) => setNewRoundNotes(e.target.value)}
                      placeholder="Round notes"
                      rows={3}
                      className="w-full rounded-md border border-gray-300 px-3 py-2"
                    />
                    <button onClick={addRound} className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
                      Add Round
                    </button>
                  </div>
                )}

                <div className="space-y-3">
                  {dailyRounds.map((round) => (
                    <div key={round.id} className="rounded-md border border-gray-200 p-3">
                      <p className="text-xs text-gray-500">{round.round_date} - {round.round_assessor_name}</p>
                      <p className="mt-1 text-sm text-gray-800">{round.round_notes}</p>
                      {round.orders && <p className="text-sm text-gray-600">Orders: {round.orders}</p>}
                    </div>
                  ))}
                  {dailyRounds.length === 0 && <p className="text-sm text-gray-500">No rounds yet.</p>}
                </div>
              </div>

              <div className="rounded-lg border border-gray-200 bg-white p-5">
                <h2 className="mb-3 text-lg font-semibold text-gray-900">Medication Administration Record</h2>
                <div className="mb-4 grid gap-2 md:grid-cols-2">
                  <input value={newMarMedicationName} onChange={(e) => setNewMarMedicationName(e.target.value)} placeholder="Medication name" className="w-full rounded-md border border-gray-300 px-3 py-2" />
                  <input value={newMarDose} onChange={(e) => setNewMarDose(e.target.value)} placeholder="Dose given" className="w-full rounded-md border border-gray-300 px-3 py-2" />
                  <input value={newMarRoute} onChange={(e) => setNewMarRoute(e.target.value)} placeholder="Route" className="w-full rounded-md border border-gray-300 px-3 py-2" />
                  <input value={newMarScheduledAt} onChange={(e) => setNewMarScheduledAt(e.target.value)} type="datetime-local" className="w-full rounded-md border border-gray-300 px-3 py-2" />
                  <input value={newMarAdministeredAt} onChange={(e) => setNewMarAdministeredAt(e.target.value)} type="datetime-local" className="w-full rounded-md border border-gray-300 px-3 py-2" />
                  <select value={newMarStatus} onChange={(e) => setNewMarStatus(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2">
                    <option value="SCHEDULED">Scheduled</option>
                    <option value="GIVEN">Given</option>
                    <option value="DELAYED">Delayed</option>
                    <option value="NOT_GIVEN">Not given</option>
                  </select>
                  <input value={newMarReasonNotGiven} onChange={(e) => setNewMarReasonNotGiven(e.target.value)} placeholder="Reason not given" className="w-full rounded-md border border-gray-300 px-3 py-2 md:col-span-2" />
                  <textarea value={newMarDeviations} onChange={(e) => setNewMarDeviations(e.target.value)} placeholder="Deviations" rows={2} className="w-full rounded-md border border-gray-300 px-3 py-2 md:col-span-2" />
                  <textarea value={newMarNotes} onChange={(e) => setNewMarNotes(e.target.value)} placeholder="Nursing notes" rows={2} className="w-full rounded-md border border-gray-300 px-3 py-2 md:col-span-2" />
                </div>
                <button onClick={addMarEntry} disabled={isMarSaving} className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:bg-gray-400">
                  {isMarSaving ? 'Saving...' : 'Add MAR Entry'}
                </button>

                <div className="mt-4 space-y-3">
                  {marEntries.map((entry) => (
                    <div key={entry.id} className="rounded-md border border-gray-200 p-3">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-gray-900">{entry.medication_name}</p>
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{entry.status}</span>
                      </div>
                      <p className="text-xs text-gray-500">Dose: {entry.dose_given} | Route: {entry.route || 'N/A'} | Scheduled: {entry.scheduled_datetime ? new Date(entry.scheduled_datetime).toLocaleString() : 'N/A'}</p>
                      <p className="text-xs text-gray-500">Administered: {entry.administered_datetime ? new Date(entry.administered_datetime).toLocaleString() : 'Not given'}{entry.administered_by_name ? ` • By ${entry.administered_by_name}` : ''}</p>
                      {entry.notes && <p className="mt-1 text-sm text-gray-700">{entry.notes}</p>}
                      {entry.reason_not_given && <p className="text-xs text-amber-700">Reason not given: {entry.reason_not_given}</p>}
                      {entry.deviations && <p className="text-xs text-rose-700">Deviations: {entry.deviations}</p>}
                    </div>
                  ))}
                  {marEntries.length === 0 && <p className="text-sm text-gray-500">No MAR entries yet.</p>}
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Discharge Package Snapshot</h2>
                  <p className="text-sm text-gray-600">Clearance state and discharge readiness for this stay.</p>
                </div>
                <Link href={`/ipd/stays/${stayId}/discharge`} className="rounded-md bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700">
                  Open Discharge Form
                </Link>
              </div>

              {dischargePackage ? (
                <div className="mt-4 grid gap-3 md:grid-cols-2">
                  <div><p className="text-xs text-gray-500">Summary</p><p className="text-sm text-gray-800 whitespace-pre-wrap">{dischargePackage.discharge_summary || 'N/A'}</p></div>
                  <div><p className="text-xs text-gray-500">Instructions</p><p className="text-sm text-gray-800 whitespace-pre-wrap">{dischargePackage.discharge_instructions || 'N/A'}</p></div>
                  <div><p className="text-xs text-gray-500">Follow-up</p><p className="text-sm text-gray-800">{dischargePackage.follow_up_date || 'N/A'}{dischargePackage.follow_up_provider ? ` • ${dischargePackage.follow_up_provider}` : ''}</p></div>
                  <div><p className="text-xs text-gray-500">Clearance</p><p className="text-sm text-gray-800">Nursing: {dischargePackage.nursing_clearance ? 'Yes' : 'No'} | Pharmacy: {dischargePackage.pharmacy_clearance ? 'Yes' : 'No'} | Billing: {dischargePackage.billing_clearance ? 'Yes' : 'No'}</p></div>
                  <div><p className="text-xs text-gray-500">Checklist</p><p className="text-sm text-gray-800">Complete: {dischargePackage.checklist_complete ? 'Yes' : 'No'} | Final approved: {dischargePackage.final_approved ? 'Yes' : 'No'}</p></div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-gray-500">No discharge package created yet.</p>
              )}
            </div>
          </>
        ) : (
          <div className="py-10 text-center text-gray-500">Stay not found.</div>
        )}
      </div>
    </ProtectedPage>
  );
}
