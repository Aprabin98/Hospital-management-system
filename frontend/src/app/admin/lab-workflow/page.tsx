'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface LabBookingWorkflowItem {
  id: number;
  patient_name: string;
  template_name: string;
  date: string;
  status: string;
  payment_status: string;
  result_id: number | null;
  is_verified: boolean;
  is_released: boolean;
  result_status: string | null;
}

type WorkflowFilter = 'ALL' | 'READY_TO_VERIFY' | 'READY_TO_RELEASE' | 'RELEASED';

function getErrorMessage(err: unknown, fallback: string) {
  if (err && typeof err === 'object' && 'message' in err && typeof (err as { message?: unknown }).message === 'string') {
    return (err as { message: string }).message;
  }
  return fallback;
}

export default function LabWorkflowPage() {
  const { userRole } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [bookings, setBookings] = useState<LabBookingWorkflowItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<WorkflowFilter>('READY_TO_RELEASE');

  const isAdmin = userRole === 'ADMIN';
  const isReceptionist = userRole === 'RECEPTIONIST';

  useEffect(() => {
    fetchWorkflow();
  }, []);

  const fetchWorkflow = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<{ count: number; results: LabBookingWorkflowItem[] }>('/lab/admin/bookings/');
      setBookings(response.results || []);
    } catch {
      toast.error('Failed to load lab workflow');
    } finally {
      setIsLoading(false);
    }
  };

  const filtered = useMemo(() => {
    if (statusFilter === 'ALL') return bookings;
    if (statusFilter === 'READY_TO_VERIFY') {
      return bookings.filter((b) => !!b.result_id && !b.is_verified);
    }
    if (statusFilter === 'READY_TO_RELEASE') {
      return bookings.filter((b) => !!b.result_id && b.is_verified && !b.is_released && b.payment_status === 'PAID');
    }
    return bookings.filter((b) => b.is_released);
  }, [bookings, statusFilter]);

  const filters: WorkflowFilter[] = isAdmin
    ? ['ALL', 'READY_TO_VERIFY', 'READY_TO_RELEASE', 'RELEASED']
    : ['READY_TO_RELEASE', 'RELEASED'];

  const verifyResult = async (resultId: number | null) => {
    if (!resultId) return;
    try {
      await apiClient.post(`/lab/results/${resultId}/verify/`, {});
      toast.success('Result verified');
      fetchWorkflow();
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Failed to verify result'));
    }
  };

  const releaseResult = async (resultId: number | null) => {
    if (!resultId) return;
    try {
      await apiClient.post(`/lab/results/${resultId}/release/`, {});
      toast.success('Result released');
      fetchWorkflow();
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Failed to release result'));
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.labWorkflow}
      title="lab workflow"
      description={isReceptionist ? 'Release verified and paid lab reports from one simple view.' : 'Verification and release workflow is restricted to administrators.'}
    >
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{isReceptionist ? 'Lab Release Workflow' : 'Lab Verification & Release Workflow'}</h1>
            <p className="mt-2 text-gray-600">
              {isReceptionist
                ? 'Release verified and paid reports. Verification remains admin-controlled.'
                : 'Verify entered reports and release only verified + paid results.'}
            </p>
          </div>
          <button onClick={fetchWorkflow} className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Refresh</button>
        </div>

        <div className="flex flex-wrap gap-2">
          {filters.map((k) => (
            <button
              key={k}
              onClick={() => setStatusFilter(k)}
              className={`rounded px-3 py-1.5 text-sm ${statusFilter === k ? 'bg-blue-600 text-white' : 'border border-gray-300 text-gray-700 hover:bg-gray-50'}`}
            >
              {k.replaceAll('_', ' ')}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading workflow...</div>
        ) : filtered.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">No records for selected filter.</div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Booking</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Patient</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Test</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Payment</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Verification</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Release</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filtered.map((b) => {
                  const canVerify = isAdmin && !!b.result_id && !b.is_verified;
                  const canRelease = !!b.result_id && b.is_verified && !b.is_released && b.payment_status === 'PAID';
                  return (
                    <tr key={b.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm text-gray-900">#{b.id}</td>
                      <td className="px-4 py-3 text-sm text-gray-900">{b.patient_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{b.template_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{b.date}</td>
                      <td className="px-4 py-3 text-sm"><span className={`rounded-full px-2 py-1 text-xs font-medium ${b.payment_status === 'PAID' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>{b.payment_status}</span></td>
                      <td className="px-4 py-3 text-sm"><span className={`rounded-full px-2 py-1 text-xs font-medium ${b.is_verified ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'}`}>{b.is_verified ? 'Verified' : 'Pending'}</span></td>
                      <td className="px-4 py-3 text-sm"><span className={`rounded-full px-2 py-1 text-xs font-medium ${b.is_released ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-700'}`}>{b.is_released ? 'Released' : 'Pending'}</span></td>
                      <td className="space-x-2 px-4 py-3 text-sm">
                        {b.result_id && (
                          <Link href={`/lab-reports/result/${b.result_id}`} className="rounded px-3 py-1 text-xs font-medium border border-slate-300 bg-white text-slate-700 hover:bg-slate-50">
                            Open Report
                          </Link>
                        )}
                        {isAdmin && (
                          <button disabled={!canVerify} onClick={() => verifyResult(b.result_id)} className={`rounded px-3 py-1 text-xs font-medium ${canVerify ? 'border border-indigo-300 bg-indigo-50 text-indigo-700 hover:bg-indigo-100' : 'cursor-not-allowed border border-gray-200 bg-gray-100 text-gray-400'}`}>Verify</button>
                        )}
                        <button disabled={!canRelease} onClick={() => releaseResult(b.result_id)} className={`rounded px-3 py-1 text-xs font-medium ${canRelease ? 'border border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100' : 'cursor-not-allowed border border-gray-200 bg-gray-100 text-gray-400'}`}>Release</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}
