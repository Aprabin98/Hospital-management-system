'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface AdmissionRequestItem {
  id: number;
  patient_name: string;
  doctor_name: string | null;
  preferred_room_number: string | null;
  preferred_room_type: string;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'ADMITTED';
  receptionist_notes: string;
  created_at: string;
}

interface RoomTransferItem {
  id: number;
  patient_name: string;
  doctor_name: string | null;
  from_room_number: string;
  from_bed_number: string;
  to_room_number: string;
  to_bed_number: string;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'COMPLETED' | 'CANCELLED';
  notes: string;
  requested_at: string;
}

interface DoctorLeaveItem {
  id: number;
  doctor_name: string;
  date: string;
  reason: string;
  approval_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  review_notes: string;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
}

interface RefundItem {
  id: number;
  payment_id: number;
  patient_name: string;
  doctor_name: string | null;
  amount: number;
  reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  notes: string;
  payment_status: string;
  created_at: string;
  refunded_at: string | null;
}

interface ReviewTarget {
  type: 'admission' | 'transfer' | 'leave' | 'refund';
  id: number;
  action: 'APPROVED' | 'REJECTED';
}

const emptyCounts = {
  admissions: 0,
  transfers: 0,
  leaves: 0,
  refunds: 0,
};

export default function ApprovalsCenterPage() {
  const [userRole] = useState(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('userRole') || '').toUpperCase();
    }
    return '';
  });
  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState(emptyCounts);
  const [admissions, setAdmissions] = useState<AdmissionRequestItem[]>([]);
  const [transfers, setTransfers] = useState<RoomTransferItem[]>([]);
  const [leaves, setLeaves] = useState<DoctorLeaveItem[]>([]);
  const [refunds, setRefunds] = useState<RefundItem[]>([]);
  const [reviewTarget, setReviewTarget] = useState<ReviewTarget | null>(null);
  const [notes, setNotes] = useState('');

  const isAdminOpsRole = userRole === 'ADMIN' || userRole === 'RECEPTIONIST';

  useEffect(() => {
    loadApprovals();
  }, []);

  const loadApprovals = async () => {
    try {
      setLoading(true);
      const [admissionsRes, transfersRes, leavesRes, refundsRes] = await Promise.all([
        apiClient.get<{ count: number; results: AdmissionRequestItem[] }>('/rooms/admission-requests/admin/?status=PENDING'),
        apiClient.get<{ count: number; results: RoomTransferItem[] }>('/rooms/transfers/?status=PENDING'),
        apiClient.get<{ count: number; results: DoctorLeaveItem[] }>('/doctor-leaves/admin/?status=PENDING'),
        apiClient.get<{ count: number; results: RefundItem[] }>('/payments/refunds/admin/?status=PENDING'),
      ]);

      setAdmissions(admissionsRes.results || []);
      setTransfers(transfersRes.results || []);
      setLeaves(leavesRes.results || []);
      setRefunds(refundsRes.results || []);
      setCounts({
        admissions: admissionsRes.count || 0,
        transfers: transfersRes.count || 0,
        leaves: leavesRes.count || 0,
        refunds: refundsRes.count || 0,
      });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load approvals');
    } finally {
      setLoading(false);
    }
  };

  const openReview = (type: ReviewTarget['type'], id: number, action: ReviewTarget['action']) => {
    setReviewTarget({ type, id, action });
    setNotes('');
  };

  const submitReview = async () => {
    if (!reviewTarget) return;

    try {
      const payload = {
        action: reviewTarget.action,
        notes,
      };

      if (reviewTarget.type === 'admission') {
        await apiClient.post(`/rooms/admission-requests/${reviewTarget.id}/review/`, payload);
      } else if (reviewTarget.type === 'transfer') {
        await apiClient.post(`/rooms/transfers/${reviewTarget.id}/review/`, payload);
      } else if (reviewTarget.type === 'leave') {
        await apiClient.post(`/doctor-leaves/${reviewTarget.id}/review/`, payload);
      } else if (reviewTarget.type === 'refund') {
        const refund = refunds.find((item) => item.id === reviewTarget.id);
        if (!refund) {
          throw new Error('Refund not found');
        }
        await apiClient.post(`/payments/${refund.payment_id}/refund/manage/`, {
          status: reviewTarget.action,
          notes,
        });
      }

      toast.success('Action completed successfully');
      setReviewTarget(null);
      setNotes('');
      loadApprovals();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to submit review');
    }
  };

  const approvalSummary = useMemo(
    () => [
      { label: 'Admissions', value: counts.admissions, tone: 'blue' },
      { label: 'Transfers', value: counts.transfers, tone: 'amber' },
      { label: 'Doctor Leaves', value: counts.leaves, tone: 'violet' },
      { label: 'Refunds', value: counts.refunds, tone: 'green' },
    ],
    [counts]
  );

  if (!isAdminOpsRole) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">Back to Dashboard</Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Approvals Center</h1>
            <p className="mt-2 text-gray-600">Review and process admissions, transfers, leave requests, and refunds from one place.</p>
          </div>
          <button onClick={loadApprovals} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Refresh</button>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {approvalSummary.map((item) => (
            <div key={item.label} className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-gray-500">{item.label}</p>
              <p className="mt-1 text-3xl font-bold text-gray-900">{item.value}</p>
            </div>
          ))}
        </div>

        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading approval queues...</div>
        ) : (
          <div className="space-y-6">
            <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">Admission Requests</h2>
              {admissions.length === 0 ? (
                <p className="mt-3 text-sm text-gray-600">No pending admission requests.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {admissions.map((item) => (
                    <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">{item.patient_name}</p>
                          <p className="text-sm text-gray-600">Doctor: {item.doctor_name || 'N/A'}</p>
                          <p className="text-sm text-gray-600">Preferred room: {item.preferred_room_number || item.preferred_room_type || 'Any available'}</p>
                          <p className="mt-1 text-sm text-gray-700">{item.reason}</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => openReview('admission', item.id, 'APPROVED')} className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700">Approve</button>
                          <button onClick={() => openReview('admission', item.id, 'REJECTED')} className="rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700">Reject</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">Room Transfers</h2>
              {transfers.length === 0 ? (
                <p className="mt-3 text-sm text-gray-600">No pending room transfer requests.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {transfers.map((item) => (
                    <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">{item.patient_name}</p>
                          <p className="text-sm text-gray-600">{item.from_room_number}-{item.from_bed_number} → {item.to_room_number}-{item.to_bed_number}</p>
                          <p className="text-sm text-gray-600">Doctor: {item.doctor_name || 'N/A'}</p>
                          <p className="mt-1 text-sm text-gray-700">{item.reason}</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => openReview('transfer', item.id, 'APPROVED')} className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700">Approve</button>
                          <button onClick={() => openReview('transfer', item.id, 'REJECTED')} className="rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700">Reject</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">Doctor Leaves</h2>
              {leaves.length === 0 ? (
                <p className="mt-3 text-sm text-gray-600">No pending leave requests.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {leaves.map((item) => (
                    <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">Dr. {item.doctor_name}</p>
                          <p className="text-sm text-gray-600">Date: {item.date}</p>
                          <p className="mt-1 text-sm text-gray-700">{item.reason || 'No reason provided'}</p>
                        </div>
                        <div className="flex gap-2">
                          {userRole === 'ADMIN' ? (
                            <>
                              <button onClick={() => openReview('leave', item.id, 'APPROVED')} className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700">Approve</button>
                              <button onClick={() => openReview('leave', item.id, 'REJECTED')} className="rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700">Reject</button>
                            </>
                          ) : (
                            <span className="rounded-lg bg-gray-100 px-3 py-2 text-sm text-gray-500">View only</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="text-xl font-semibold text-gray-900">Refund Requests</h2>
              {refunds.length === 0 ? (
                <p className="mt-3 text-sm text-gray-600">No pending refund requests.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {refunds.map((item) => (
                    <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                      <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">{item.patient_name}</p>
                          <p className="text-sm text-gray-600">Payment #{item.payment_id} • ₹{item.amount}</p>
                          <p className="text-sm text-gray-600">Status: {item.payment_status}</p>
                          <p className="mt-1 text-sm text-gray-700">{item.reason}</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => openReview('refund', item.id, 'APPROVED')} className="rounded-lg bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700">Approve</button>
                          <button onClick={() => openReview('refund', item.id, 'REJECTED')} className="rounded-lg bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700">Reject</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </div>

      {reviewTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
            <h3 className="text-xl font-bold text-gray-900">Confirm {reviewTarget.action}</h3>
            <p className="mt-2 text-sm text-gray-600">Add optional notes before submitting this approval action.</p>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={4}
              className="mt-4 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 placeholder:text-gray-500"
              placeholder="Notes"
            />
            <div className="mt-5 flex justify-end gap-3">
              <button onClick={() => setReviewTarget(null)} className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
              <button onClick={submitReview} className={`rounded-lg px-4 py-2 font-medium text-white ${reviewTarget.action === 'APPROVED' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}`}>
                Submit
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
