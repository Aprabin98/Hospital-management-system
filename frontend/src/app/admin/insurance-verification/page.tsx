'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface InsuranceItem {
  id: number;
  patient_id: number;
  patient: string;
  provider_name: string;
  policy_number: string;
  plan_name: string;
  coverage_percent: number;
  status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'EXPIRED';
  valid_until: string | null;
  verification_notes: string;
  external_reference: string;
}

type InsuranceFilter = 'ALL' | InsuranceItem['status'];

function getErrorMessage(err: unknown, fallback: string) {
  if (err && typeof err === 'object' && 'message' in err && typeof (err as { message?: unknown }).message === 'string') {
    return (err as { message: string }).message;
  }
  return fallback;
}

export default function InsuranceVerificationPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [items, setItems] = useState<InsuranceItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<InsuranceFilter>('ALL');

  const [activeItemId, setActiveItemId] = useState<number | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<InsuranceItem['status']>('VERIFIED');
  const [verifyNotes, setVerifyNotes] = useState('');
  const [verifyRef, setVerifyRef] = useState('');

  useEffect(() => {
    fetchInsurance();
  }, []);

  const fetchInsurance = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<{ count: number; results: InsuranceItem[] }>('/payments/insurance/');
      setItems(response.results || []);
    } catch {
      toast.error('Failed to load insurance records');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredItems = useMemo(() => {
    if (statusFilter === 'ALL') return items;
    return items.filter((item) => item.status === statusFilter);
  }, [items, statusFilter]);

  const openVerifyPanel = (item: InsuranceItem) => {
    setActiveItemId(item.id);
    setVerifyStatus(item.status === 'PENDING' ? 'VERIFIED' : item.status);
    setVerifyNotes(item.verification_notes || '');
    setVerifyRef(item.external_reference || '');
  };

  const submitVerification = async () => {
    if (!activeItemId) return;
    try {
      await apiClient.post(`/payments/insurance/${activeItemId}/verify/`, {
        status: verifyStatus,
        verification_notes: verifyNotes,
        external_reference: verifyRef,
      });
      toast.success('Insurance status updated');
      setActiveItemId(null);
      fetchInsurance();
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Failed to update insurance status'));
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Insurance Verification Workflow</h1>
            <p className="mt-2 text-gray-600">Review patient insurance claims and update verification outcomes.</p>
          </div>
          <button onClick={fetchInsurance} className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Refresh</button>
        </div>

        <div className="flex flex-wrap gap-2">
          {(['ALL', 'PENDING', 'VERIFIED', 'REJECTED', 'EXPIRED'] as InsuranceFilter[]).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`rounded px-3 py-1.5 text-sm ${statusFilter === status ? 'bg-blue-600 text-white' : 'border border-gray-300 text-gray-700 hover:bg-gray-50'}`}
            >
              {status}
            </button>
          ))}
        </div>

        {isLoading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading insurance queue...</div>
        ) : filteredItems.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">No insurance records found for selected filter.</div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Patient</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Provider</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Policy</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Coverage</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Valid Until</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredItems.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{item.patient}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.provider_name}<div className="text-xs text-gray-500">{item.plan_name || 'No plan name'}</div></td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.policy_number}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.coverage_percent}%</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.valid_until || '-'}</td>
                    <td className="px-4 py-3 text-sm"><span className={`rounded-full px-2 py-1 text-xs font-medium ${item.status === 'VERIFIED' ? 'bg-green-100 text-green-700' : item.status === 'REJECTED' ? 'bg-red-100 text-red-700' : item.status === 'EXPIRED' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'}`}>{item.status}</span></td>
                    <td className="px-4 py-3 text-sm">
                      <button onClick={() => openVerifyPanel(item)} className="rounded border border-indigo-300 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100">Review / Verify</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeItemId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
              <h2 className="mb-4 text-xl font-bold text-gray-900">Update Verification</h2>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Status</label>
                  <select value={verifyStatus} onChange={(e) => setVerifyStatus(e.target.value as InsuranceItem['status'])} className="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900">
                    <option value="PENDING">PENDING</option>
                    <option value="VERIFIED">VERIFIED</option>
                    <option value="REJECTED">REJECTED</option>
                    <option value="EXPIRED">EXPIRED</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Verification Notes</label>
                  <textarea value={verifyNotes} onChange={(e) => setVerifyNotes(e.target.value)} rows={3} className="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">External Reference</label>
                  <input value={verifyRef} onChange={(e) => setVerifyRef(e.target.value)} className="mt-1 w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900" />
                </div>
              </div>
              <div className="mt-5 flex gap-3">
                <button onClick={() => setActiveItemId(null)} className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                <button onClick={submitVerification} className="flex-1 rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700">Save</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
