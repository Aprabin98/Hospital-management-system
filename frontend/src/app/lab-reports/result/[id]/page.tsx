'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { useAuth } from '@/hooks';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

const BACKEND_ORIGIN = process.env.NEXT_PUBLIC_API_URL
  ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/?$/, '')
  : 'http://localhost:8000';

function getBackendFileUrl(path?: string | null) {
  if (!path) {
    return '';
  }
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${BACKEND_ORIGIN}${path.startsWith('/') ? '' : '/'}${path}`;
}

type ResultItem = {
  id: number;
  field: number;
  field_name: string;
  unit: string;
  value: string | null;
  status: string;
  is_critical: boolean;
};

type ResultDetails = {
  id: number;
  status: string;
  notes: string;
  pdf_file?: string | null;
  pdf_url?: string | null;
  is_released: boolean;
  has_critical_values: boolean;
  filled_at?: string;
  booking_info?: {
    patient_name?: string;
    template_name?: string;
    date?: string;
  };
  items?: ResultItem[];
};

export default function ResultDetailsPage() {
  const params = useParams<{ id?: string | string[] }>();
  const resultId = typeof params?.id === 'string' ? params.id : '';
  const { userRole, isLoading: authLoading } = useAuth();
  const role = (userRole || '').toUpperCase();
  const [result, setResult] = useState<ResultDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [draftNotes, setDraftNotes] = useState('');
  const [draftItems, setDraftItems] = useState<Array<{ field: number; field_name: string; unit: string; value: string }>>([]);

  const canEdit = role === 'ADMIN' || (role === 'LAB_TECHNICIAN' && !result?.is_released);

  const fetchResultDetails = useCallback(async () => {
    if (!resultId) {
      setError('Invalid result id');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiClient.get<ResultDetails>(`/lab/results/${resultId}/`);
      setResult(response);
    } catch (err: any) {
      setError(err?.message || 'Failed to load result details');
      toast.error('Failed to load result details');
    } finally {
      setIsLoading(false);
    }
  }, [resultId]);

  useEffect(() => {
    void fetchResultDetails();
  }, [fetchResultDetails]);

  useEffect(() => {
    if (!result) {
      return;
    }

    setDraftNotes(result.notes || '');
    setDraftItems((result.items || []).map((item) => ({
      field: item.field,
      field_name: item.field_name,
      unit: item.unit,
      value: item.value || '',
    })));
  }, [result]);

  const saveReportDetails = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!result || !canEdit) {
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.patch(`/lab/results/${result.id}/`, {
        notes: draftNotes,
        items: draftItems.map((item) => ({ field: item.field, value: item.value })),
      });
      toast.success('Report details saved');
      await fetchResultDetails();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to save report details');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading || authLoading) {
    return (
      <MainLayout>
        <div className="flex h-64 items-center justify-center">
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </MainLayout>
    );
  }

  if (error || !result) {
    return (
      <MainLayout>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          {error || 'Result not found'}
        </div>
        <Link href="/lab-reports" className="mt-4 inline-block text-blue-600 hover:text-blue-700">
          ← Back to Lab Reports
        </Link>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Link href="/lab-reports" className="mb-2 inline-block font-medium text-blue-600 hover:text-blue-700">
              ← Back to Lab Reports
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Test Result Details</h1>
            <p className="mt-2 text-gray-600">
              {canEdit ? 'Fill or update the report details below.' : 'View the released lab report information.'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-600">Result Status</p>
            <p className="mt-2 inline-block rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-800">
              {result.status}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <p className="text-sm text-gray-600">Result Released</p>
            <p className="mt-2 text-lg font-semibold text-gray-900">{result.is_released ? '✓ Yes' : 'Pending'}</p>
          </div>

          <div className={`rounded-lg border p-6 shadow-sm ${result.has_critical_values ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'}`}>
            <p className={`text-sm ${result.has_critical_values ? 'text-red-600' : 'text-green-600'}`}>Critical Values</p>
            <p className={`mt-2 text-lg font-semibold ${result.has_critical_values ? 'text-red-900' : 'text-green-900'}`}>
              {result.has_critical_values ? '⚠️ Critical' : 'Normal'}
            </p>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-xl font-bold text-gray-900">Result Information</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <p className="text-sm text-gray-600">Patient</p>
              <p className="text-lg font-semibold text-gray-900">{result.booking_info?.patient_name || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Test Name</p>
              <p className="text-lg font-semibold text-gray-900">{result.booking_info?.template_name || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Test Date</p>
              <p className="text-lg font-semibold text-gray-900">{result.booking_info?.date || 'Unknown'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Filled At</p>
              <p className="text-lg font-semibold text-gray-900">{result.filled_at ? new Date(result.filled_at).toLocaleString() : 'Not set'}</p>
            </div>
          </div>
        </div>

        {canEdit && (
          <form onSubmit={saveReportDetails} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="text-xl font-bold text-gray-900">Fill Report Details</h2>
              <button
                type="submit"
                disabled={isSaving}
                className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
              >
                {isSaving ? 'Saving...' : 'Save Report Details'}
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">Technician Notes</label>
                <textarea
                  value={draftNotes}
                  onChange={(event) => setDraftNotes(event.target.value)}
                  rows={4}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none"
                  placeholder="Enter report notes"
                />
              </div>

              <div>
                <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">Result Fields</h3>
                {draftItems.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-gray-300 bg-gray-50 p-4 text-sm text-gray-600">
                    No result fields are available for this report.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {draftItems.map((item, index) => (
                      <div key={item.field} className="grid gap-3 rounded-lg border border-gray-200 p-4 md:grid-cols-[1.5fr_1fr] md:items-center">
                        <div>
                          <p className="font-semibold text-gray-900">{item.field_name}</p>
                          <p className="text-sm text-gray-500">{item.unit || 'No unit'}</p>
                        </div>
                        <input
                          value={item.value}
                          onChange={(event) => {
                            const nextItems = [...draftItems];
                            nextItems[index] = { ...item, value: event.target.value };
                            setDraftItems(nextItems);
                          }}
                          className="rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none"
                          placeholder="Enter value"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </form>
        )}

        {result.items && result.items.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-xl font-bold text-gray-900">Test Results</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Parameter</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Value</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Unit</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{item.field_name}</td>
                      <td className="px-6 py-4 text-sm font-semibold text-gray-900">{item.value || '—'}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{item.unit || '—'}</td>
                      <td className="px-6 py-4 text-sm">
                        <span
                          className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
                            item.is_critical
                              ? 'bg-red-100 text-red-800'
                              : item.status === 'NORMAL'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {item.status || (item.is_critical ? 'Critical' : 'Normal')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {result.notes && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-xl font-bold text-gray-900">Comments</h2>
            <p className="whitespace-pre-wrap text-gray-700">{result.notes}</p>
          </div>
        )}

        {result.pdf_file && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-xl font-bold text-gray-900">Report Document</h2>
            <div className="flex flex-wrap gap-3">
              <a
                href={getBackendFileUrl(result.pdf_url || result.pdf_file)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition-colors hover:bg-blue-700"
              >
                View PDF Report
              </a>
              <a
                href={getBackendFileUrl(result.pdf_url || result.pdf_file)}
                download
                className="inline-flex items-center gap-2 rounded-lg bg-green-600 px-6 py-2 font-medium text-white transition-colors hover:bg-green-700"
              >
                Download PDF Report
              </a>
            </div>
          </div>
        )}

        <div className="flex gap-4">
          <Link href="/lab-reports" className="rounded-lg bg-blue-600 px-6 py-2 font-medium text-white transition-colors hover:bg-blue-700">
            Back to Lab Reports
          </Link>
        </div>
      </div>
    </MainLayout>
  );
}