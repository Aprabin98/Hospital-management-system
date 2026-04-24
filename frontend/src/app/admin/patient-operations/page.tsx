'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface PatientItem {
  id: number;
  full_name: string;
  phone: string;
  gender: string;
  blood_group: string;
  date_of_birth: string | null;
  created_at: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
}

interface PatientsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PatientItem[];
}

const PAGE_SIZE = 15;

function downloadCsv(filename: string, rows: string[][]) {
  const csvContent = rows
    .map((row) => row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','))
    .join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export default function PatientOperationsPage() {
  const [loading, setLoading] = useState(true);
  const [queryInput, setQueryInput] = useState('');
  const [query, setQuery] = useState('');
  const [page, setPage] = useState(1);
  const [patients, setPatients] = useState<PatientItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);

  const loadPatients = async (targetPage: number, targetQuery: string) => {
    try {
      setLoading(true);
      const params: Record<string, string | number> = {
        page: targetPage,
        page_size: PAGE_SIZE,
      };

      if (targetQuery.trim()) {
        params.q = targetQuery.trim();
      }

      const response = await apiClient.get<PatientsResponse>('/patients/', { params });
      setPatients(response.results || []);
      setTotalCount(response.count || 0);
      setPage(targetPage);
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load patients');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatients(1, '');
  }, []);

  const pageCount = useMemo(() => Math.max(1, Math.ceil(totalCount / PAGE_SIZE)), [totalCount]);

  const onSearch = () => {
    setQuery(queryInput);
    loadPatients(1, queryInput);
  };

  const exportCurrentPage = () => {
    if (patients.length === 0) {
      toast.error('No rows to export');
      return;
    }

    const rows: string[][] = [
      ['Patient ID', 'Full Name', 'Email', 'Phone', 'Gender', 'Blood Group', 'Date of Birth', 'Created At'],
      ...patients.map((patient) => [
        String(patient.id),
        patient.full_name || `${patient.user?.first_name || ''} ${patient.user?.last_name || ''}`.trim(),
        patient.user?.email || '-',
        patient.phone || '-',
        patient.gender || '-',
        patient.blood_group || '-',
        patient.date_of_birth || '-',
        patient.created_at ? new Date(patient.created_at).toISOString() : '-',
      ]),
    ];

    downloadCsv(`patient-ops-page-${page}.csv`, rows);
    toast.success('CSV exported');
  };

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Patient Operations</h1>
            <p className="mt-2 text-gray-600">Search patient records quickly, review profiles, and export operational data.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={exportCurrentPage} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
              Export CSV
            </button>
            <Link href="/patients/create" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
              Add Patient
            </Link>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-500">Total Patients</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{totalCount}</p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-500">Current Page</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{page}</p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-500">Page Size</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{PAGE_SIZE}</p>
          </div>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row">
            <input
              value={queryInput}
              onChange={(e) => setQueryInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  onSearch();
                }
              }}
              placeholder="Search by name, email, phone, blood group, or patient ID"
              className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder:text-gray-500"
            />
            <button onClick={onSearch} className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-black">
              Search
            </button>
            <button
              onClick={() => {
                setQueryInput('');
                setQuery('');
                loadPatients(1, '');
              }}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Clear
            </button>
          </div>
          {query ? <p className="mt-3 text-sm text-gray-600">Active filter: {query}</p> : null}
        </div>

        <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Patient Directory</h2>
            <Link href="/patients" className="text-sm font-medium text-blue-600 hover:text-blue-800">
              Open full patients page
            </Link>
          </div>

          {loading ? (
            <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading patients...</div>
          ) : patients.length === 0 ? (
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-8 text-center text-gray-600">No patients found for this filter.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">ID</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">Patient</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">Contact</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">Clinical</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {patients.map((patient) => (
                    <tr key={patient.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-700">#{patient.id}</td>
                      <td className="px-4 py-3">
                        <p className="text-sm font-semibold text-gray-900">{patient.full_name || `${patient.user?.first_name || ''} ${patient.user?.last_name || ''}`.trim() || 'Unknown'}</p>
                        <p className="text-xs text-gray-500">Created {new Date(patient.created_at).toLocaleDateString()}</p>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        <p>{patient.user?.email || '-'}</p>
                        <p>{patient.phone || '-'}</p>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        <p>Gender: {patient.gender || '-'}</p>
                        <p>Blood: {patient.blood_group || '-'}</p>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-2">
                          <Link href={`/patients/${patient.id}`} className="rounded-md border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700 hover:bg-blue-100">
                            View
                          </Link>
                          <Link href={`/billing?status=UNPAID`} className="rounded-md border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700 hover:bg-amber-100">
                            Billing
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="mt-5 flex items-center justify-between gap-4">
            <p className="text-sm text-gray-600">Page {page} of {pageCount}</p>
            <div className="flex gap-2">
              <button
                onClick={() => loadPatients(page - 1, query)}
                disabled={page <= 1 || loading}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <button
                onClick={() => loadPatients(page + 1, query)}
                disabled={page >= pageCount || loading}
                className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </section>
      </div>
    </MainLayout>
  );
}
