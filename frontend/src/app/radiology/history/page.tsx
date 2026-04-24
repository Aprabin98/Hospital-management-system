'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useRoleAccess } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';
import { EmptyState, PageHeader, SectionCard, StatusBadge } from '@/components/UI';

interface ImagingHistoryItem {
  id: number;
  patient_name: string;
  catalog_name: string;
  modality: string;
  priority: string;
  status: string;
  released_at: string | null;
  report?: {
    impression?: string;
    report_status?: string;
    is_critical?: boolean;
  };
}

interface PatientOption {
  id: number;
  full_name: string;
}

export default function ImagingHistoryPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [patientQuery, setPatientQuery] = useState('');
  const [patientOptions, setPatientOptions] = useState<PatientOption[]>([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const [history, setHistory] = useState<ImagingHistoryItem[]>([]);

  const { canAccess, userRole } = useRoleAccess(ACCESS_MATRIX.radiologyHistory);
  const isPatient = userRole === 'PATIENT';

  const searchPatients = useCallback(async (query: string) => {
    if (!query.trim() || isPatient) {
      setPatientOptions([]);
      return;
    }

    try {
      const data = await apiClient.get<{ results: PatientOption[] }>(`/patients/?q=${encodeURIComponent(query)}&page_size=8`);
      setPatientOptions(data.results || []);
    } catch {
      setPatientOptions([]);
    }
  }, [isPatient]);

  const loadHistory = useCallback(async () => {
    try {
      setIsLoading(true);
      const query = isPatient ? '' : `?patient_id=${encodeURIComponent(selectedPatient)}`;
      const data = await apiClient.get<ImagingHistoryItem[]>(`/radiology/history/${query}`);
      setHistory(data || []);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to load imaging history');
      setHistory([]);
    } finally {
      setIsLoading(false);
    }
  }, [isPatient, selectedPatient]);

  useEffect(() => {
    if (!canAccess) return;
    if (isPatient) {
      void loadHistory();
    }
  }, [canAccess, isPatient, loadHistory]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      void searchPatients(patientQuery);
    }, 250);
    return () => clearTimeout(timeout);
  }, [patientQuery, searchPatients]);

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.radiologyHistory}
      title="imaging history"
      description="Imaging history is restricted to approved clinical access roles."
    >
      <div className="space-y-6">
        <PageHeader
          title="Imaging History"
          description="View released radiology results and report impressions."
          actions={
            <Link href="/radiology" className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
              Back to Radiology
            </Link>
          }
        />

        {!isPatient && (
          <SectionCard title="Select Patient" subtitle="Staff users must select a patient before loading history.">
            <div className="grid gap-3 md:grid-cols-3">
              <div className="md:col-span-2">
                <input
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={patientQuery}
                  onChange={(e) => {
                    setPatientQuery(e.target.value);
                    setSelectedPatient('');
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
                          setSelectedPatient(String(patient.id));
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
                <button
                  type="button"
                  onClick={loadHistory}
                  disabled={!selectedPatient || isLoading}
                  className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
                >
                  {isLoading ? 'Loading...' : 'Load History'}
                </button>
              </div>
            </div>
          </SectionCard>
        )}

        <SectionCard title="Released Imaging Studies" subtitle="Only reported and released studies are shown.">
          {isLoading ? (
            <div className="p-6 text-center text-gray-500">Loading imaging history...</div>
          ) : history.length === 0 ? (
            <EmptyState title="No imaging history" description="Released imaging reports will appear here." />
          ) : (
            <div className="divide-y divide-gray-100">
              {history.map((item) => (
                <div key={item.id} className="px-4 py-4">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-gray-900">IMG-{item.id} {item.patient_name}</p>
                    <StatusBadge value={item.status} />
                    {item.report?.is_critical ? <StatusBadge value="CRITICAL" /> : null}
                  </div>
                  <p className="text-sm text-gray-700">{item.catalog_name} ({item.modality})</p>
                  {item.report?.impression ? <p className="mt-1 text-xs text-gray-600">Impression: {item.report.impression}</p> : null}
                  <p className="mt-1 text-xs text-gray-500">
                    Released: {item.released_at ? new Date(item.released_at).toLocaleString() : 'Not released'}
                  </p>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </ProtectedPage>
  );
}
