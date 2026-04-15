'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks';
import toast from 'react-hot-toast';

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<any>(null);
  const { userRole } = useAuth();
  const [tests, setTests] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [selectedTestId, setSelectedTestId] = useState('');
  const [reason, setReason] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const canRecommend = ['admin', 'doctor', 'receptionist'].includes((userRole || '').toLowerCase());

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get(`/patients/${id}/`);
        setPatient(response);
        await Promise.all([fetchTests(), fetchRecommendations()]);
      } catch (err: any) {
        toast.error(err?.message || 'Failed to load patient details');
      } finally {
        setIsLoading(false);
      }
    };
    if (id) load();
  }, [id]);

  const fetchTests = async () => {
    try {
      const response = await apiClient.get<{ results?: any[] } | any[]>('/lab/tests/');
      setTests(Array.isArray(response) ? response : response.results || []);
    } catch {
      setTests([]);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const response = await apiClient.get<{ results?: any[] }>(`/lab/recommendations/?page_size=100`);
      setRecommendations(response.results || []);
    } catch {
      setRecommendations([]);
    }
  };

  const handleRecommendTest = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!selectedTestId) {
      toast.error('Select a test to recommend');
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.post('/lab/recommendations/create/', {
        patient: id,
        template: selectedTestId,
        reason,
        priority,
      });
      toast.success('Test recommended successfully');
      setSelectedTestId('');
      setReason('');
      setPriority('MEDIUM');
      fetchRecommendations();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to recommend test');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Link href="/patients" className="text-blue-600 hover:text-blue-700 font-medium">← Back to Patients</Link>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">Patient Details</h1>
        </div>

        {isLoading && <p className="text-gray-600">Loading patient details...</p>}

        {!isLoading && !patient && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">Patient not found.</div>
        )}

        {patient && (
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-500">Full Name</p>
                <p className="text-lg font-semibold text-gray-900">{patient.full_name || `${patient.user?.first_name || ''} ${patient.user?.last_name || ''}`.trim() || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Email</p>
                <p className="text-lg font-semibold text-gray-900">{patient.user?.email || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Phone</p>
                <p className="text-lg font-semibold text-gray-900">{patient.phone || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Blood Group</p>
                <p className="text-lg font-semibold text-gray-900">{patient.blood_group || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Date of Birth</p>
                <p className="text-lg font-semibold text-gray-900">{patient.date_of_birth || '-'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Emergency Contact</p>
                <p className="text-lg font-semibold text-gray-900">{patient.emergency_contact || '-'}</p>
              </div>
            </div>

            <div className="mt-6">
              <p className="text-sm text-gray-500">Address</p>
              <p className="text-gray-800">{patient.address || '-'}</p>
            </div>

            {canRecommend && (
              <form onSubmit={handleRecommendTest} className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-4">
                <h2 className="text-lg font-semibold text-blue-900">Recommend Lab Test</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <select
                    value={selectedTestId}
                    onChange={(e) => setSelectedTestId(e.target.value)}
                    className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900"
                  >
                    <option value="">Select test</option>
                    {tests.map((test: any) => (
                      <option key={test.id} value={test.id}>
                        {test.name} - ₹{test.price}
                      </option>
                    ))}
                  </select>

                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900"
                  >
                    <option value="LOW">Low Priority</option>
                    <option value="MEDIUM">Medium Priority</option>
                    <option value="HIGH">High Priority</option>
                  </select>

                  <button
                    type="submit"
                    disabled={isSaving}
                    className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400"
                  >
                    {isSaving ? 'Saving...' : 'Recommend Test'}
                  </button>
                </div>

                <textarea
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  rows={3}
                  placeholder="Reason for recommending this test"
                  className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900"
                />

                <p className="text-xs text-blue-800">
                  Available tests are loaded from the backend lab catalog. Doctors can recommend one directly for this patient.
                </p>
              </form>
            )}

            <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">Recommended Tests</h2>
              {recommendations.length === 0 ? (
                <p className="text-sm text-gray-600">No test recommendations yet.</p>
              ) : (
                <div className="space-y-3">
                  {recommendations
                    .filter((rec: any) => String(rec.patient) === String(id))
                    .map((rec: any) => (
                      <div key={rec.id} className="rounded-lg border border-gray-200 bg-white p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <p className="font-semibold text-gray-900">{rec.test_name}</p>
                            <p className="text-sm text-gray-600">Priority: {rec.priority} • Status: {rec.status}</p>
                          </div>
                          <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-800">
                            {rec.recommended_by_name || 'Staff'}
                          </span>
                        </div>
                        {rec.reason && <p className="mt-2 text-sm text-gray-700">{rec.reason}</p>}
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
