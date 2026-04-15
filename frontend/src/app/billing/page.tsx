'use client';

import { Suspense, useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface Payment {
  id: number;
  payment_type: string;
  patient_name: string;
  doctor_name: string;
  amount: number;
  amount_paid: number;
  amount_remaining: number;
  status: string;
  payment_method: string;
  paid_at: string | null;
  due_date: string | null;
  appointment_id: number | null;
  lab_booking_id: number | null;
  lab_booking_name: string | null;
  is_overdue: boolean;
  overdue_days: number;
  notes: string;
  has_refund_request: boolean;
  refund_status: string | null;
  created_at: string;
}

interface Stats {
  total_amount: number;
  total_paid: number;
  total_unpaid: number;
  total_refunded: number;
  payment_count: number;
  paid_count: number;
  unpaid_count: number;
  overdue_count: number;
}

interface PaymentsApiResponse {
  count: number;
  page: number;
  page_size: number;
  total_paid: number;
  total_unpaid: number;
  results: Payment[];
}

interface RevenueSummary {
  total_revenue: number;
  total_transactions: number;
  total_refunded_amount: number;
  pending_refund_count: number;
  net_revenue: number;
}

const getErrorMessage = (err: unknown, fallback: string) => {
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return fallback;
};

const BillingPageContent = () => {
  const searchParams = useSearchParams();
  const [payments, setPayments] = useState<Payment[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState(() => (searchParams.get('status') || '').toUpperCase());
  const [userRole, setUserRole] = useState('');
  const [revenueSummary, setRevenueSummary] = useState<RevenueSummary | null>(null);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [refundReason, setRefundReason] = useState('');
  const [submittingRefund, setSubmittingRefund] = useState(false);
  const [selectedRefundReviewPayment, setSelectedRefundReviewPayment] = useState<Payment | null>(null);
  const [showRefundReviewModal, setShowRefundReviewModal] = useState(false);
  const [refundDecision, setRefundDecision] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [refundReviewNotes, setRefundReviewNotes] = useState('');
  const [submittingRefundReview, setSubmittingRefundReview] = useState(false);

  const isPatient = userRole === 'PATIENT';
  const canManageBilling = userRole === 'ADMIN' || userRole === 'RECEPTIONIST';
  const canManageRefunds = userRole === 'ADMIN';

  // Fetch payments and stats
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError('');

      const paymentsParams: Record<string, string | number> = { page_size: 50 };
      if (statusFilter) {
        paymentsParams.status = statusFilter;
      }

      const [paymentsRes, statsRes, revenueRes] = await Promise.all([
        apiClient.get<PaymentsApiResponse>('/payments/', { params: paymentsParams }),
        apiClient.get<Stats>('/payments/stats/'),
        userRole === 'ADMIN' ? apiClient.get<RevenueSummary>('/payments/revenue/') : Promise.resolve(null),
      ]) as [PaymentsApiResponse, Stats, RevenueSummary | null];

      setPayments(paymentsRes.results || []);
      setStats(statsRes);
      setRevenueSummary(revenueRes);
    } catch (err: unknown) {
      const message = getErrorMessage(err, 'Failed to load billing information');
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, userRole]);

  useEffect(() => {
    setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
  }, []);

  useEffect(() => {
    if (!userRole) {
      return;
    }
    fetchData();
  }, [fetchData, userRole]);

  const handleRequestRefund = (payment: Payment) => {
    if (!isPatient) {
      setError('Only patients can request refunds.');
      return;
    }
    if (payment.status !== 'PAID') {
      setError('Only paid payments can be refunded.');
      return;
    }
    setSelectedPayment(payment);
    setShowRefundModal(true);
  };

  const markAsPaid = async (payment: Payment) => {
    if (!canManageBilling) {
      setError('Access denied.');
      return;
    }

    try {
      await apiClient.post(`/payments/${payment.id}/mark-paid/`, {
        payment_method: payment.payment_method || 'CASH',
      });
      toast.success(`Payment #${payment.id} marked as paid`);
      await fetchData();
    } catch (err: unknown) {
      const message = getErrorMessage(err, 'Failed to mark payment as paid');
      setError(message);
      toast.error(message);
    }
  };

  const openRefundReviewModal = (payment: Payment) => {
    if (!canManageRefunds) {
      setError('Only admin can manage refunds.');
      return;
    }
    setSelectedRefundReviewPayment(payment);
    setRefundDecision('APPROVED');
    setRefundReviewNotes('');
    setShowRefundReviewModal(true);
  };

  const submitRefundReview = async () => {
    if (!selectedRefundReviewPayment) {
      return;
    }

    try {
      setSubmittingRefundReview(true);
      await apiClient.post(`/payments/${selectedRefundReviewPayment.id}/refund/manage/`, {
        status: refundDecision,
        notes: refundReviewNotes,
      });
      toast.success(`Refund ${refundDecision.toLowerCase()} successfully`);
      setShowRefundReviewModal(false);
      setSelectedRefundReviewPayment(null);
      await fetchData();
    } catch (err: unknown) {
      const message = getErrorMessage(err, 'Failed to process refund request');
      setError(message);
      toast.error(message);
    } finally {
      setSubmittingRefundReview(false);
    }
  };

  const submitRefundRequest = async () => {
    if (!selectedPayment || !refundReason.trim()) {
      setError('Please provide a refund reason.');
      return;
    }

    try {
      setSubmittingRefund(true);
      await apiClient.post(`/payments/${selectedPayment.id}/refund/`, {
        reason: refundReason,
      });
      toast.success('Refund request submitted');

      // Reset and refresh
      setShowRefundModal(false);
      setRefundReason('');
      setSelectedPayment(null);
      await fetchData();
    } catch (err: unknown) {
      const message = getErrorMessage(err, 'Failed to submit refund request');
      setError(message);
      toast.error(message);
    } finally {
      setSubmittingRefund(false);
    }
  };

  const downloadInvoice = async (paymentId: number) => {
    try {
      const token = localStorage.getItem('authToken');
      const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/payments/${paymentId}/invoice/`, {
        method: 'GET',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        let message = 'Failed to download bill PDF';
        try {
          const payload = await response.json();
          message = payload?.detail || payload?.message || message;
        } catch {
          // Non-JSON response body.
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `receipt_${paymentId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const message = getErrorMessage(err, 'Failed to download invoice');
      setError(message);
      toast.error(message);
    }
  };

  const getStatusBadgeClass = (status: string): string => {
    switch (status) {
      case 'PAID':
        return 'bg-emerald-100 text-emerald-700';
      case 'UNPAID':
        return 'bg-amber-100 text-amber-700';
      case 'OVERDUE':
        return 'bg-rose-100 text-rose-700';
      case 'REFUNDED':
        return 'bg-cyan-100 text-cyan-700';
      default:
        return 'bg-slate-100 text-slate-700';
    }
  };

  const getPaymentTypeIcon = (type: string) => {
    switch (type) {
      case 'APPOINTMENT':
        return '🏥';
      case 'LAB_TEST':
        return '🧪';
      case 'ADMISSION':
        return '🏨';
      case 'CONSULTATION':
        return '💬';
      default:
        return '💰';
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Billing & Payments</h1>
            <p className="mt-1 text-gray-600">
              {canManageBilling
                ? 'Admin billing control panel for payment and refund operations'
                : 'Manage your payment history and invoices'}
            </p>
          </div>
          <Link
            href="/dashboard"
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back to Dashboard
          </Link>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="rounded-xl border border-gray-200 bg-white p-10 text-center text-gray-500 shadow-sm">
            Loading billing information...
          </div>
        ) : (
          <>
            {stats && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-xl bg-gradient-to-br from-sky-600 to-blue-700 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Total Amount</p>
                  <p className="mt-2 text-2xl font-bold">Rs. {stats.total_amount.toFixed(2)}</p>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Paid ({stats.paid_count})</p>
                  <p className="mt-2 text-2xl font-bold">Rs. {stats.total_paid.toFixed(2)}</p>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Unpaid ({stats.unpaid_count})</p>
                  <p className="mt-2 text-2xl font-bold">Rs. {stats.total_unpaid.toFixed(2)}</p>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-rose-500 to-red-600 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Overdue Payments</p>
                  <p className="mt-2 text-2xl font-bold">{stats.overdue_count}</p>
                </div>
              </div>
            )}

            {canManageBilling && revenueSummary && (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-700 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Net Revenue</p>
                  <p className="mt-2 text-2xl font-bold">Rs. {Number(revenueSummary.net_revenue).toFixed(2)}</p>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-cyan-600 to-sky-700 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Gross Revenue</p>
                  <p className="mt-2 text-2xl font-bold">Rs. {Number(revenueSummary.total_revenue).toFixed(2)}</p>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Refunded Amount</p>
                  <p className="mt-2 text-2xl font-bold">Rs. {Number(revenueSummary.total_refunded_amount).toFixed(2)}</p>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-rose-500 to-red-600 p-4 text-white shadow-sm">
                  <p className="text-sm opacity-85">Pending Refund Requests</p>
                  <p className="mt-2 text-2xl font-bold">{revenueSummary.pending_refund_count}</p>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              {isPatient && (
                <div className="mb-3 rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs text-blue-700">
                  <span className="font-semibold">Note:</span> Invoice means your bill PDF. Download is available when status is PAID.
                </div>
              )}
              {canManageBilling && (
                <div className="mb-3 rounded-lg border border-indigo-100 bg-indigo-50 px-3 py-2 text-xs text-indigo-700">
                  <span className="font-semibold">Admin Note:</span> Use Mark as Paid for pending payments and Manage Refund for pending refund requests.
                </div>
              )}
              <p className="mb-3 text-sm font-semibold text-gray-700">Filter by Status</p>
              <div className="flex flex-wrap gap-2">
                {['', 'UNPAID', 'PAID', 'OVERDUE', 'REFUNDED'].map((status) => {
                  const selected = statusFilter === status;
                  const label = status || 'ALL';
                  return (
                    <button
                      key={label}
                      onClick={() => setStatusFilter(status)}
                      className={[
                        'rounded-full border px-4 py-1.5 text-xs font-semibold transition',
                        selected
                          ? 'border-blue-600 bg-blue-600 text-white'
                          : 'border-gray-300 bg-white text-gray-700 hover:border-blue-300 hover:text-blue-700',
                      ].join(' ')}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
              <div className="border-b border-gray-200 px-4 py-3">
                <h2 className="text-lg font-semibold text-gray-900">Payment History</h2>
              </div>
              {payments.length === 0 ? (
                <div className="p-10 text-center text-gray-500">No payments found.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">ID</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Type</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Details</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Amount</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Date</th>
                        <th className="px-4 py-3 text-left font-semibold text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 bg-white">
                      {payments.map((payment) => (
                        <tr key={payment.id} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-semibold text-gray-900">#{payment.id}</td>
                          <td className="px-4 py-3 text-gray-700">
                            {getPaymentTypeIcon(payment.payment_type)} {payment.payment_type.replace('_', ' ')}
                          </td>
                          <td className="px-4 py-3 text-gray-600">
                            {payment.payment_type === 'APPOINTMENT' && payment.doctor_name
                              ? `Dr. ${payment.doctor_name}`
                              : payment.lab_booking_name || 'N/A'}
                          </td>
                          <td className="px-4 py-3 text-gray-900">
                            <p className="font-semibold">Rs. {Number(payment.amount).toFixed(2)}</p>
                            {Number(payment.amount_remaining) > 0 && (
                              <p className="text-xs text-gray-500">
                                Remaining: Rs. {Number(payment.amount_remaining).toFixed(2)}
                              </p>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${getStatusBadgeClass(payment.status)}`}>
                              {payment.status}
                            </span>
                            {payment.is_overdue && (
                              <p className="mt-1 text-xs text-rose-600">{payment.overdue_days} days overdue</p>
                            )}
                          </td>
                          <td className="px-4 py-3 text-gray-600">
                            {payment.paid_at
                              ? new Date(payment.paid_at).toLocaleDateString()
                              : payment.due_date
                                ? new Date(payment.due_date).toLocaleDateString()
                                : '-'}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <Link
                                href={`/billing/${payment.id}`}
                                className="rounded-md border border-gray-300 px-2.5 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50"
                              >
                                View
                              </Link>
                              <button
                                onClick={() => downloadInvoice(payment.id)}
                                disabled={payment.status !== 'PAID'}
                                title={payment.status === 'PAID' ? 'Download paid bill PDF' : 'Available after payment is marked as PAID'}
                                className={[
                                  'rounded-md px-2.5 py-1 text-xs font-medium',
                                  payment.status === 'PAID'
                                    ? 'border border-emerald-300 text-emerald-700 hover:bg-emerald-50'
                                    : 'cursor-not-allowed border border-gray-200 text-gray-400',
                                ].join(' ')}
                              >
                                Download Bill PDF
                              </button>
                              {isPatient && payment.status === 'PAID' && !payment.has_refund_request && (
                                <button
                                  onClick={() => handleRequestRefund(payment)}
                                  className="rounded-md border border-rose-300 px-2.5 py-1 text-xs font-medium text-rose-700 hover:bg-rose-50"
                                >
                                  Request Refund
                                </button>
                              )}
                              {isPatient && payment.has_refund_request && (
                                <span className="rounded-md bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">
                                  Refund: {payment.refund_status || 'PENDING'}
                                </span>
                              )}
                              {canManageBilling && ['UNPAID', 'OVERDUE', 'PARTIALLY_PAID'].includes(payment.status) && (
                                <button
                                  onClick={() => markAsPaid(payment)}
                                  className="rounded-md border border-blue-300 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-50"
                                >
                                  Mark as Paid
                                </button>
                              )}
                              {canManageRefunds && payment.refund_status === 'PENDING' && (
                                <button
                                  onClick={() => openRefundReviewModal(payment)}
                                  className="rounded-md border border-violet-300 px-2.5 py-1 text-xs font-medium text-violet-700 hover:bg-violet-50"
                                >
                                  Manage Refund
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}

        {showRefundModal && selectedPayment && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
              <h3 className="text-lg font-semibold text-gray-900">Request Refund</h3>
              <p className="mt-1 text-sm text-gray-600">
                Payment #{selectedPayment.id} • Rs. {Number(selectedPayment.amount).toFixed(2)}
              </p>

              <label className="mt-4 block text-sm font-medium text-gray-700">Refund reason</label>
              <textarea
                value={refundReason}
                onChange={(e) => setRefundReason(e.target.value)}
                rows={4}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="Describe why you need this refund"
              />

              <div className="mt-4 flex justify-end gap-2">
                <button
                  onClick={() => {
                    setShowRefundModal(false);
                    setRefundReason('');
                    setSelectedPayment(null);
                  }}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  disabled={submittingRefund}
                >
                  Cancel
                </button>
                <button
                  onClick={submitRefundRequest}
                  disabled={submittingRefund || !refundReason.trim()}
                  className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submittingRefund ? 'Submitting...' : 'Submit'}
                </button>
              </div>
            </div>
          </div>
        )}

        {showRefundReviewModal && selectedRefundReviewPayment && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl">
              <h3 className="text-lg font-semibold text-gray-900">Manage Refund Request</h3>
              <p className="mt-1 text-sm text-gray-600">
                Payment #{selectedRefundReviewPayment.id} • Rs. {Number(selectedRefundReviewPayment.amount).toFixed(2)}
              </p>

              <label className="mt-4 block text-sm font-medium text-gray-700">Decision</label>
              <select
                value={refundDecision}
                onChange={(e) => setRefundDecision(e.target.value as 'APPROVED' | 'REJECTED')}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="APPROVED">Approve</option>
                <option value="REJECTED">Reject</option>
              </select>

              <label className="mt-4 block text-sm font-medium text-gray-700">Admin notes (optional)</label>
              <textarea
                value={refundReviewNotes}
                onChange={(e) => setRefundReviewNotes(e.target.value)}
                rows={3}
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                placeholder="Add notes for the refund decision"
              />

              <div className="mt-4 flex justify-end gap-2">
                <button
                  onClick={() => {
                    setShowRefundReviewModal(false);
                    setSelectedRefundReviewPayment(null);
                  }}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  disabled={submittingRefundReview}
                >
                  Cancel
                </button>
                <button
                  onClick={submitRefundReview}
                  disabled={submittingRefundReview}
                  className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submittingRefundReview ? 'Saving...' : 'Save Decision'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
};

const BillingPage = () => {
  return (
    <Suspense
      fallback={
        <MainLayout>
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-gray-600 shadow-sm">
            Loading billing...
          </div>
        </MainLayout>
      }
    >
      <BillingPageContent />
    </Suspense>
  );
};

export default BillingPage;
