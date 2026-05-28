'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

type ResultItem = {
  id: number;
  field: number;
  field_name: string;
  unit: string;
  normal_min?: string | number | null;
  normal_max?: string | number | null;
  normal_text?: string | null;
  is_required?: boolean;
  value: string | null;
  status: string;
  is_critical: boolean;
};

type LabResult = {
  id: number;
  status: string;
  notes: string;
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

type PendingResult = {
  id: number;
  patient_name: string;
  template_name: string;
  date: string;
  status: string;
};

function formatDate(value?: string) {
  if (!value) {
    return 'Not set';
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

function formatRange(item: ResultItem) {
  if (item.normal_min !== null && item.normal_min !== undefined && item.normal_max !== null && item.normal_max !== undefined) {
    return `${item.normal_min} - ${item.normal_max}`;
  }

  if (item.normal_text) {
    return item.normal_text;
  }

  return '—';
}

export default function LabResultsInputPage() {
  const [pendingResults, setPendingResults] = useState<PendingResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<LabResult | null>(null);
  const [draftNotes, setDraftNotes] = useState('');
  const [draftItems, setDraftItems] = useState<Array<{ field: number; field_name: string; unit: string; normal_min?: string | number | null; normal_max?: string | number | null; normal_text?: string | null; is_required?: boolean; value: string }>>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const fetchPendingResults = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<any>('/lab/results/');
      const results = Array.isArray(response) ? response : response?.results || [];

      const pending = results
        .filter((result: any) => result.status === 'PENDING' || result.status === 'ENTERED')
        .map((result: any) => ({
          id: result.id,
          patient_name: result.booking_info?.patient_name || 'Unknown',
          template_name: result.booking_info?.template_name || 'Unknown',
          date: result.booking_info?.date || '',
          status: result.status,
        }));

      setPendingResults(pending);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to load pending results');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchPendingResults();
  }, [fetchPendingResults]);

  const openResult = async (resultId: number) => {
    try {
      const response = await apiClient.get<LabResult>(`/lab/results/${resultId}/`);
      setSelectedResult(response);
      setDraftNotes(response.notes || '');
      setDraftItems((response.items || []).map((item) => ({
        field: item.field,
        field_name: item.field_name,
        unit: item.unit,
        normal_min: item.normal_min,
        normal_max: item.normal_max,
        normal_text: item.normal_text,
        is_required: item.is_required,
        value: item.value || '',
      })));
    } catch (error: any) {
      toast.error(error?.message || 'Failed to load result details');
    }
  };

  const closeEditor = () => {
    setSelectedResult(null);
    setDraftNotes('');
    setDraftItems([]);
  };

  const saveResults = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!selectedResult) {
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.patch(`/lab/results/${selectedResult.id}/`, {
        notes: draftNotes,
        items: draftItems.map((item) => ({ field: item.field, value: item.value })),
        status: 'ENTERED',
      });
      toast.success('Lab results saved');
      closeEditor();
      await fetchPendingResults();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to save results');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <section className="rounded-[1.75rem] border border-emerald-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="mb-2 inline-flex rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
                Lab Technician Workspace
              </p>
              <h1 className="text-3xl font-bold text-slate-950">Fill Lab Results</h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-600">
                Enter test parameters such as blood sugar, CBC fields, and other lab values using the backend result fields.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void fetchPendingResults()}
                className="rounded-2xl border border-slate-900 bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
              >
                {isLoading ? 'Refreshing...' : 'Refresh List'}
              </button>
              <Link href="/lab-dashboard" className="rounded-2xl border border-emerald-200 bg-emerald-50 px-5 py-3 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-100">
                Back to Lab Dashboard
              </Link>
              <Link href="/lab-reports?tab=results" className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50">
                Open Lab Reports
              </Link>
            </div>
          </div>
        </section>

        {!selectedResult ? (
          <section className="rounded-[1.75rem] border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-6 py-4">
              <h2 className="text-lg font-bold text-slate-900">Pending Test Bookings</h2>
              <p className="mt-1 text-sm text-slate-600">Select a booking to fill its result fields.</p>
            </div>

            {isLoading ? (
              <div className="px-6 py-12 text-sm text-slate-500">Loading pending results...</div>
            ) : pendingResults.length === 0 ? (
              <div className="px-6 py-12 text-sm text-slate-500">No pending lab results are available.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Patient</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Test</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Status</th>
                      <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {pendingResults.map((result) => (
                      <tr key={result.id} className="hover:bg-slate-50/80">
                        <td className="px-6 py-4 text-sm text-slate-900">{result.patient_name}</td>
                        <td className="px-6 py-4 text-sm text-slate-900">{result.template_name}</td>
                        <td className="px-6 py-4 text-sm text-slate-600">{formatDate(result.date)}</td>
                        <td className="px-6 py-4 text-sm">
                          <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800">
                            {result.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <button
                            type="button"
                            onClick={() => void openResult(result.id)}
                            className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-700 transition hover:bg-emerald-100"
                          >
                            Fill Results
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        ) : (
          <section className="rounded-[1.75rem] border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-6 py-4">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div>
                  <h2 className="text-xl font-bold text-slate-900">Fill Results - {selectedResult.booking_info?.template_name || 'Lab Test'}</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Patient: {selectedResult.booking_info?.patient_name || 'Unknown'} | Date: {formatDate(selectedResult.booking_info?.date)}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={closeEditor}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Back to List
                </button>
              </div>
            </div>

            <form onSubmit={saveResults} className="space-y-6 p-6">
              <div className="rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">Test Parameters</h3>
                    <p className="mt-1 text-sm text-slate-600">
                      Leave a value blank if the parameter was not performed. The report will show an em dash for empty values.
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                    <span className="rounded-full bg-white px-3 py-1 text-slate-700">{selectedResult.booking_info?.patient_name || 'Unknown patient'}</span>
                    <span className="rounded-full bg-white px-3 py-1 text-slate-700">{selectedResult.booking_info?.template_name || 'Lab test'}</span>
                    <span className={`rounded-full px-3 py-1 ${selectedResult.has_critical_values ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700'}`}>
                      {selectedResult.has_critical_values ? 'Critical values present' : 'No critical values'}
                    </span>
                  </div>
                </div>

                <div className="mt-5 space-y-4">
                  {draftItems.length === 0 ? (
                    <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-4 py-10 text-center text-sm text-slate-500">
                      No result fields are available for this report.
                    </div>
                  ) : (
                    draftItems.map((item, index) => (
                      <div key={item.field} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                        <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <h4 className="text-base font-semibold text-slate-900">{item.field_name}</h4>
                              {item.is_required ? (
                                <span className="rounded-full bg-rose-100 px-2.5 py-1 text-[11px] font-semibold text-rose-700">Required</span>
                              ) : (
                                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">Optional</span>
                              )}
                            </div>
                            <div className="mt-2 grid gap-2 text-sm text-slate-600 sm:grid-cols-3">
                              <p><span className="font-semibold text-slate-700">Normal Range:</span> {formatRange(item as ResultItem)}</p>
                              <p><span className="font-semibold text-slate-700">Unit:</span> {item.unit || '—'}</p>
                              <p><span className="font-semibold text-slate-700">Field ID:</span> #{item.field}</p>
                            </div>
                          </div>

                          <div className="w-full xl:max-w-md">
                            <label className="mb-2 block text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                              Enter Value
                            </label>
                            <input
                              type="text"
                              value={item.value}
                              onChange={(event) => {
                                const nextItems = [...draftItems];
                                nextItems[index] = { ...item, value: event.target.value };
                                setDraftItems(nextItems);
                              }}
                              className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-400"
                              placeholder={item.is_required ? 'Required value' : 'Leave blank if not done'}
                              required={Boolean(item.is_required)}
                            />
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <label className="mb-2 block text-sm font-semibold text-slate-900">Lab Notes</label>
                <textarea
                  value={draftNotes}
                  onChange={(event) => setDraftNotes(event.target.value)}
                  rows={4}
                  className="w-full rounded-2xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-emerald-400"
                  placeholder="Add optional technician notes"
                />
              </div>

              <div className="flex flex-wrap gap-3 border-t border-slate-200 pt-4">
                <button
                  type="submit"
                  disabled={isSaving}
                  className="rounded-2xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-400"
                >
                  {isSaving ? 'Saving...' : 'Save Results & Generate PDF'}
                </button>
                <button
                  type="button"
                  onClick={closeEditor}
                  className="rounded-2xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          </section>
        )}
      </div>
    </MainLayout>
  );
}
