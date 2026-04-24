'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface LabSample {
  id: number;
  result_id: number;
  barcode_id: string;
  status: 'COLLECTED' | 'IN_PROCESS' | 'VALIDATED' | 'RELEASED' | 'REJECTED' | 'RECOLLECT';
  collected_by_name: string | null;
  collected_at: string | null;
  processed_by_name: string | null;
  processed_at: string | null;
  validated_by_name: string | null;
  validated_at: string | null;
  rejection_reason: string;
  recollect_reason: string;
  created_at: string;
  updated_at: string;
}

interface SampleListResponse {
  count: number;
  results: LabSample[];
}

const STATUS_COLORS: Record<string, string> = {
  COLLECTED: 'bg-blue-100 text-blue-800',
  IN_PROCESS: 'bg-yellow-100 text-yellow-800',
  VALIDATED: 'bg-green-100 text-green-800',
  RELEASED: 'bg-purple-100 text-purple-800',
  REJECTED: 'bg-red-100 text-red-800',
  RECOLLECT: 'bg-orange-100 text-orange-800',
};

export default function LabSamplesPage() {
  const [samples, setSamples] = useState<LabSample[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [newStatus, setNewStatus] = useState<string>('');
  const [selectedSample, setSelectedSample] = useState<LabSample | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [rejectionReason, setRejectionReason] = useState('');
  const [recollectReason, setRecollectReason] = useState('');

  const { userRole } = useAuth();
  const canManageSamples = useMemo(
    () => ACCESS_MATRIX.labOperations.includes((userRole || '').toUpperCase() as (typeof ACCESS_MATRIX.labOperations)[number]),
    [userRole]
  );

  useEffect(() => {
    const run = async () => {
      try {
        setIsLoading(true);
        const url = statusFilter ? `/lab/samples/?status=${statusFilter}` : '/lab/samples/';
        const response = await apiClient.get<SampleListResponse>(url);
        setSamples(response.results || []);
      } catch (error) {
        toast.error('Failed to load lab samples');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };
    run();
  }, [statusFilter]);

  const handleUpdateStatus = async () => {
    if (!selectedSample || !newStatus) {
      toast.error('Please select a status');
      return;
    }

    try {
      setIsUpdating(true);
      const payload: any = { status: newStatus };
      if (newStatus === 'REJECTED') payload.rejection_reason = rejectionReason;
      if (newStatus === 'RECOLLECT') payload.recollect_reason = recollectReason;

      const updated = await apiClient.patch<LabSample>(`/lab/samples/${selectedSample.id}/`, payload);
      setSamples(samples.map(s => s.id === updated.id ? updated : s));
      setSelectedSample(null);
      setNewStatus('');
      setRejectionReason('');
      setRecollectReason('');
      toast.success('Sample status updated');
    } catch (error) {
      toast.error('Failed to update sample status');
      console.error(error);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.labOperations}
      title="lab sample tracking"
      description="Sample handling is restricted to laboratory operations roles."
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Lab Sample Tracking</h1>
            <p className="mt-2 text-gray-600">Phase 4: Complete sample traceability with barcode IDs</p>
          </div>
        </div>

        {/* Status Filter */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Filter by Status</h3>
          <div className="grid grid-cols-2 gap-2 md:grid-cols-6">
            {['', 'COLLECTED', 'IN_PROCESS', 'VALIDATED', 'RELEASED', 'REJECTED', 'RECOLLECT'].map(status => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`rounded px-3 py-2 text-sm font-medium transition ${
                  statusFilter === status
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {status || 'All'}
              </button>
            ))}
          </div>
        </div>

        {/* Samples List */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Barcode ID</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Collected By</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Validated By</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-900">Created At</th>
                  {canManageSamples && <th className="px-4 py-3 text-left font-semibold text-gray-900">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {isLoading ? (
                  <tr>
                    <td colSpan={canManageSamples ? 6 : 5} className="px-4 py-8 text-center text-gray-500">
                      Loading samples...
                    </td>
                  </tr>
                ) : samples.length === 0 ? (
                  <tr>
                    <td colSpan={canManageSamples ? 6 : 5} className="px-4 py-8 text-center text-gray-500">
                      No samples found
                    </td>
                  </tr>
                ) : (
                  samples.map(sample => (
                    <tr key={sample.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-gray-900">{sample.barcode_id}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${STATUS_COLORS[sample.status]}`}>
                          {sample.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{sample.collected_by_name || '—'}</td>
                      <td className="px-4 py-3 text-gray-600">{sample.validated_by_name || '—'}</td>
                      <td className="px-4 py-3 text-gray-600">{new Date(sample.created_at).toLocaleString()}</td>
                      {canManageSamples && (
                        <td className="px-4 py-3">
                          <button
                            onClick={() => setSelectedSample(sample)}
                            className="text-indigo-600 hover:underline"
                          >
                            Update
                          </button>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Sample Update Panel */}
        {selectedSample && (
          <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Update Sample Status</h2>
            <p className="mt-1 text-sm text-gray-600">Barcode: {selectedSample.barcode_id}</p>

            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">New Status</label>
                <select
                  value={newStatus}
                  onChange={e => setNewStatus(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                >
                  <option value="">Select status</option>
                  <option value="IN_PROCESS">In Process</option>
                  <option value="VALIDATED">Validated</option>
                  <option value="RELEASED">Released</option>
                  <option value="REJECTED">Rejected</option>
                  <option value="RECOLLECT">Recollect</option>
                </select>
              </div>

              {newStatus === 'REJECTED' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Rejection Reason</label>
                  <textarea
                    value={rejectionReason}
                    onChange={e => setRejectionReason(e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    rows={2}
                    placeholder="Explain why the sample was rejected"
                  />
                </div>
              )}

              {newStatus === 'RECOLLECT' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Recollection Reason</label>
                  <textarea
                    value={recollectReason}
                    onChange={e => setRecollectReason(e.target.value)}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    rows={2}
                    placeholder="Explain why recollection is needed"
                  />
                </div>
              )}

              <div className="flex gap-2">
                <button
                  onClick={handleUpdateStatus}
                  disabled={isUpdating}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:bg-indigo-300"
                >
                  Update
                </button>
                <button
                  onClick={() => {
                    setSelectedSample(null);
                    setNewStatus('');
                    setRejectionReason('');
                    setRecollectReason('');
                  }}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}
