'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface Payment {
  id: number;
  payment_type: string;
  patient_name: string;
  patient_email: string;
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
  created_at: string;
  updated_at: string;
}

const BillingDetailPage = () => {
  const params = useParams<{ id?: string | string[] }>();
  const paymentId = typeof params?.id === 'string' ? params.id : '';
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [userRole, setUserRole] = useState('');
  const [processing, setProcessing] = useState(false);

  const isPatient = userRole === 'PATIENT';
  const canManageBilling = userRole === 'ADMIN' || userRole === 'RECEPTIONIST';

  useEffect(() => {
    setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
  }, []);

  useEffect(() => {
    if (!paymentId) {
      setLoading(false);
      setError('Invalid payment id');
      return;
    }

    const fetchPayment = async () => {
      try {
        setLoading(true);
        const res = await apiClient.get<Payment>(`/payments/${paymentId}/`);
        setPayment(res);
      } catch (err: any) {
        const message = err?.message || 'Failed to load payment details';
        setError(message);
        toast.error(message);
      } finally {
        setLoading(false);
      }
    };

    fetchPayment();
  }, [paymentId]);

  const downloadInvoice = async () => {
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
    } catch (err: any) {
      const message = err?.message || 'Failed to download invoice';
      setError(message);
      toast.error(message);
    }
  };

  const markAsPaid = async () => {
    if (!payment) {
      return;
    }
    try {
      setProcessing(true);
      const updated = await apiClient.post<Payment>(`/payments/${payment.id}/mark-paid/`, {
        payment_method: payment.payment_method || 'CASH',
      });
      setPayment(updated);
      toast.success('Payment marked as paid');
    } catch (err: any) {
      const message = err?.message || 'Failed to mark payment as paid';
      setError(message);
      toast.error(message);
    } finally {
      setProcessing(false);
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

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Payment Details</h1>
            <p className="mt-1 text-gray-600">Invoice and transaction information</p>
          </div>
          <Link
            href="/billing"
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Back to Billing
          </Link>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="rounded-xl border border-gray-200 bg-white p-10 text-center text-gray-500 shadow-sm">
            Loading payment details...
          </div>
        ) : !payment ? (
          <div className="rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">
            Payment not found.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Payment ID</p>
                    <h2 className="text-2xl font-bold text-gray-900">#{payment.id}</h2>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs font-semibold ${getStatusBadgeClass(payment.status)}`}>
                    {payment.status}
                  </span>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Service Type</p>
                    <p className="mt-1 font-semibold text-gray-900">{payment.payment_type.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Provider</p>
                    <p className="mt-1 font-semibold text-gray-900">
                      {payment.payment_type === 'APPOINTMENT' && payment.doctor_name
                        ? `Dr. ${payment.doctor_name}`
                        : payment.lab_booking_name || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Created</p>
                    <p className="mt-1 text-gray-800">{new Date(payment.created_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Due Date</p>
                    <p className="mt-1 text-gray-800">{payment.due_date ? new Date(payment.due_date).toLocaleDateString() : '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Paid Date</p>
                    <p className="mt-1 text-gray-800">{payment.paid_at ? new Date(payment.paid_at).toLocaleString() : '-'}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Payment Method</p>
                    <p className="mt-1 text-gray-800">{payment.payment_method || '-'}</p>
                  </div>
                </div>

                {payment.notes && (
                  <div className="mt-4 rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                    <p className="font-semibold text-gray-800">Notes</p>
                    <p className="mt-1">{payment.notes}</p>
                  </div>
                )}

                {payment.is_overdue && (
                  <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                    This payment is {payment.overdue_days} days overdue.
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <p className="text-xs uppercase tracking-wide text-gray-500">Total Amount</p>
                <p className="mt-1 text-3xl font-bold text-gray-900">Rs. {Number(payment.amount).toFixed(2)}</p>

                <p className="mt-4 text-xs uppercase tracking-wide text-gray-500">Amount Paid</p>
                <p className="mt-1 text-xl font-semibold text-emerald-600">Rs. {Number(payment.amount_paid).toFixed(2)}</p>

                <p className="mt-4 text-xs uppercase tracking-wide text-gray-500">Remaining</p>
                <p className="mt-1 text-xl font-semibold text-amber-600">Rs. {Number(payment.amount_remaining).toFixed(2)}</p>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-800">Actions</h3>
                {isPatient && <p className="mt-1 text-xs text-gray-500">Invoice means bill PDF.</p>}
                <div className="mt-3 space-y-2">
                  {payment.status === 'PAID' ? (
                    <button
                      onClick={downloadInvoice}
                      className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                    >
                      Download Bill PDF
                    </button>
                  ) : (
                    <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-700">
                      Bill PDF will be available after payment is marked as PAID.
                    </div>
                  )}

                  {canManageBilling && ['UNPAID', 'OVERDUE', 'PARTIALLY_PAID'].includes(payment.status) && (
                    <button
                      onClick={markAsPaid}
                      disabled={processing}
                      className="w-full rounded-lg border border-blue-300 px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {processing ? 'Updating...' : 'Mark as Paid'}
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
};

export default BillingDetailPage;
