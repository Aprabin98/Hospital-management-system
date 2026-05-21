'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks';

const emptyVisit = {
  symptoms: '',
  diagnosis: '',
  doctor_notes: '',
  prescribed_medicines: '',
  suggested_tests: '',
  follow_up_date: '',
};

export default function PatientDetailPage() {
  const params = useParams<{ id?: string | string[] }>();
  const id = typeof params?.id === 'string' ? params.id : '';
  const { userRole } = useAuth();
  const role = (userRole || '').toLowerCase();
  const canEdit = ['admin', 'doctor', 'nurse'].includes(role);
  const canUpload = ['admin', 'doctor', 'nurse', 'receptionist', 'lab_technician'].includes(role);

  const [patient, setPatient] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [tests, setTests] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [visit, setVisit] = useState(emptyVisit);
  const [selectedTestId, setSelectedTestId] = useState('');
  const [reason, setReason] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [docFile, setDocFile] = useState<File | null>(null);
  const [docTitle, setDocTitle] = useState('');
  const [profileDateOfBirth, setProfileDateOfBirth] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  const load = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const [patientRes, timelineRes, summaryRes, testsRes, recRes] = await Promise.all([
        apiClient.get(`/patients/${id}/`),
        apiClient.get(`/patients/${id}/timeline/`),
        apiClient.get(`/patients/${id}/care-summary/`),
        apiClient.get<any>('/lab/tests/'),
        apiClient.get<any>('/lab/recommendations/?page_size=100'),
      ]);
      setPatient(patientRes);
      setProfileDateOfBirth(patientRes?.date_of_birth || '');
      setTimeline(timelineRes);
      setSummary(summaryRes);
      setTests(Array.isArray(testsRes) ? testsRes : testsRes.results || []);
      setRecommendations((recRes.results || []).filter((r: any) => String(r.patient) === String(id)));
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load patient');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const saveVisit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!visit.symptoms.trim()) return toast.error('Symptoms required');
    try {
      setSaving(true);
      await apiClient.post('/patient-visits/', {
        patient: id,
        ...visit,
        follow_up_date: visit.follow_up_date || null,
      });
      toast.success('Visit saved with AI suggestions');
      setVisit(emptyVisit);
      load();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to save visit');
    } finally {
      setSaving(false);
    }
  };

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canEdit) return;

    try {
      setSavingProfile(true);
      const updated = await apiClient.patch(`/patients/${id}/`, {
        date_of_birth: profileDateOfBirth || null,
      });
      setPatient(updated);
      setProfileDateOfBirth(updated?.date_of_birth || '');
      toast.success('Patient date of birth updated');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to update patient date of birth');
    } finally {
      setSavingProfile(false);
    }
  };

  const recommendTest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTestId) return toast.error('Select test');
    await apiClient.post('/lab/recommendations/create/', { patient: id, template: selectedTestId, reason, priority });
    toast.success('Test recommended');
    setSelectedTestId('');
    setReason('');
    load();
  };

  const uploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!docFile || !docTitle.trim()) return toast.error('Title and file required');
    const form = new FormData();
    form.append('patient', id);
    form.append('title', docTitle);
    form.append('document_type', 'OTHER');
    form.append('file', docFile);
    await apiClient.post('/patient-documents/', form, { headers: { 'Content-Type': 'multipart/form-data' } });
    toast.success('Document uploaded');
    setDocTitle('');
    setDocFile(null);
    load();
  };

  const completeFollowup = async (visitId: number) => {
    await apiClient.post(`/patient-followups/${visitId}/complete/`);
    toast.success('Follow-up completed');
    load();
  };

  if (loading) return <MainLayout><p className="text-gray-600">Loading patient...</p></MainLayout>;

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Link href="/patients" className="font-medium text-blue-600 hover:text-blue-700">Back to Patients</Link>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">Patient Management</h1>
        </div>

        <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{patient?.full_name || timeline?.patient?.name}</h2>
              <p className="text-sm text-gray-600">{patient?.user?.email || '-'} | {patient?.phone || '-'}</p>
              <p className="text-sm text-gray-600">Blood: {patient?.blood_group || '-'} | DOB: {patient?.date_of_birth || '-'} | Emergency: {patient?.emergency_contact || '-'}</p>
            </div>
            <span className={`rounded-full px-3 py-1 text-sm font-semibold ${
              summary?.risk_flag === 'HIGH' ? 'bg-red-100 text-red-700' :
              summary?.risk_flag === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'
            }`}>
              Risk: {summary?.risk_flag || 'LOW'}
            </span>
          </div>
          <p className="mt-4 rounded-lg bg-blue-50 p-3 text-sm text-blue-800">{summary?.summary}</p>
        </section>

        {canEdit && (
          <form onSubmit={saveProfile} className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
            <h3 className="text-lg font-semibold text-emerald-900">Edit Patient Date of Birth</h3>
            <p className="mt-1 text-sm text-emerald-800">Use this to add or update the patient DOB from the frontend.</p>
            <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto] md:items-end">
              <div>
                <label className="mb-2 block text-sm font-medium text-emerald-900">Date of Birth</label>
                <input
                  type="date"
                  value={profileDateOfBirth}
                  onChange={(e) => setProfileDateOfBirth(e.target.value)}
                  className="w-full rounded-lg border border-emerald-300 bg-white p-3 text-sm text-gray-900"
                />
              </div>
              <button
                type="submit"
                disabled={savingProfile}
                className="rounded-lg bg-emerald-600 px-4 py-3 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {savingProfile ? 'Saving...' : 'Save DOB'}
              </button>
            </div>
          </form>
        )}

        <section className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <h3 className="font-semibold text-gray-900">Care Summary</h3>
            <p className="mt-2 text-sm text-gray-600">Allergies: {(summary?.active_allergies || []).join(', ') || 'None'}</p>
            <p className="text-sm text-gray-600">Chronic: {summary?.chronic_conditions || 'Not recorded'}</p>
            <p className="text-sm text-gray-600">Medicines: {summary?.current_medications || 'Not recorded'}</p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <h3 className="font-semibold text-gray-900">Recommended Tests</h3>
            {(summary?.recommended_tests || []).length ? summary.recommended_tests.map((t: string) => <p key={t} className="text-sm text-gray-600">{t}</p>) : <p className="text-sm text-gray-600">None yet</p>}
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <h3 className="font-semibold text-gray-900">Pending Follow-ups</h3>
            {(summary?.pending_followups || []).length ? summary.pending_followups.map((f: any) => (
              <div key={f.id} className="mt-2 flex items-center justify-between gap-2 text-sm">
                <span>{f.follow_up_date}</span>
                {canEdit && <button onClick={() => completeFollowup(f.id)} className="text-blue-600">Complete</button>}
              </div>
            )) : <p className="text-sm text-gray-600">No pending follow-up</p>}
          </div>
        </section>

        {canEdit && (
          <form onSubmit={saveVisit} className="rounded-xl border border-blue-200 bg-blue-50 p-5">
            <h3 className="text-lg font-semibold text-blue-900">Add Visit Record + AI Analysis</h3>
            <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
              <textarea className="rounded-lg border p-3" rows={3} placeholder="Symptoms" value={visit.symptoms} onChange={e => setVisit({ ...visit, symptoms: e.target.value })} />
              <textarea className="rounded-lg border p-3" rows={3} placeholder="Diagnosis" value={visit.diagnosis} onChange={e => setVisit({ ...visit, diagnosis: e.target.value })} />
              <textarea className="rounded-lg border p-3" rows={3} placeholder="Doctor notes" value={visit.doctor_notes} onChange={e => setVisit({ ...visit, doctor_notes: e.target.value })} />
              <textarea className="rounded-lg border p-3" rows={3} placeholder="Medicines" value={visit.prescribed_medicines} onChange={e => setVisit({ ...visit, prescribed_medicines: e.target.value })} />
              <input className="rounded-lg border p-3" placeholder="Suggested tests" value={visit.suggested_tests} onChange={e => setVisit({ ...visit, suggested_tests: e.target.value })} />
              <input className="rounded-lg border p-3" type="date" value={visit.follow_up_date} onChange={e => setVisit({ ...visit, follow_up_date: e.target.value })} />
            </div>
            <button disabled={saving} className="mt-3 rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white disabled:bg-gray-400">{saving ? 'Saving...' : 'Save Visit'}</button>
          </form>
        )}

        <section className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="text-lg font-semibold text-gray-900">Patient Visit Timeline</h3>
          <div className="mt-3 space-y-3">
            {(timeline?.visits || []).map((v: any) => (
              <div key={v.id} className="rounded-lg border border-gray-200 p-4">
                <div className="flex flex-wrap justify-between gap-2">
                  <p className="font-semibold text-gray-900">{new Date(v.visit_date).toLocaleString()}</p>
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{v.ai_risk_level}</span>
                </div>
                <p className="mt-2 text-sm text-gray-700">Symptoms: {v.symptoms}</p>
                {v.ai_possible_causes && <p className="text-sm text-gray-700">AI causes: {v.ai_possible_causes.replaceAll('\n', ', ')}</p>}
                {v.ai_recommended_tests && <p className="text-sm text-gray-700">AI tests: {v.ai_recommended_tests.replaceAll('\n', ', ')}</p>}
                {v.ai_red_flags && <p className="text-sm text-red-700">Warnings: {v.ai_red_flags.replaceAll('\n', ', ')}</p>}
              </div>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <form onSubmit={recommendTest} className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="font-semibold text-gray-900">Recommend Lab Test</h3>
            <select className="mt-3 w-full rounded-lg border p-2" value={selectedTestId} onChange={e => setSelectedTestId(e.target.value)}>
              <option value="">Select test</option>
              {tests.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
            <select className="mt-3 w-full rounded-lg border p-2" value={priority} onChange={e => setPriority(e.target.value)}>
              <option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option>
            </select>
            <textarea className="mt-3 w-full rounded-lg border p-2" rows={2} placeholder="Reason" value={reason} onChange={e => setReason(e.target.value)} />
            <button className="mt-3 rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white">Recommend</button>
            {recommendations.map((r: any) => <p key={r.id} className="mt-2 text-sm text-gray-600">{r.test_name} - {r.status}</p>)}
          </form>

          <div className="rounded-xl border border-gray-200 bg-white p-5">
            <h3 className="font-semibold text-gray-900">Document Vault</h3>
            {canUpload && (
              <form onSubmit={uploadDocument} className="mt-3 space-y-2">
                <input className="w-full rounded-lg border p-2" placeholder="Document title" value={docTitle} onChange={e => setDocTitle(e.target.value)} />
                <input className="w-full rounded-lg border p-2" type="file" onChange={e => setDocFile(e.target.files?.[0] || null)} />
                <button className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white">Upload</button>
              </form>
            )}
            <div className="mt-3 space-y-2">
              {(timeline?.documents || []).map((d: any) => (
                <a key={d.id} href={d.file_url} target="_blank" className="block rounded-lg border p-3 text-sm text-blue-700">{d.title} ({d.document_type})</a>
              ))}
            </div>
          </div>
        </section>
      </div>
    </MainLayout>
  );
}
