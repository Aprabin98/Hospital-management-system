'use client';

import React, { useEffect, useMemo, useState } from 'react';

import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface Payment {
  id: number;
  amount: number;
  patient_email: string;
  appointment_date: string;
  status: 'PENDING' | 'PAID' | 'FAILED' | 'REFUNDED' | 'OVERDUE';
  created_at: string;
}

export default function PaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<Payment>>('/payments/');
      setPayments(response.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payments');
      toast.error('Failed to load payments');
    } finally {
      setIsLoading(false);
    }
  };

  const statusColors: { [key: string]: string } = {
    PENDING: 'bg-yellow-100 text-yellow-800',
    PAID: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
    REFUNDED: 'bg-blue-100 text-blue-800',
    OVERDUE: 'bg-red-100 text-red-800',
  };

  const filteredPayments = useMemo(() => {
    let result = payments;

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter((p) =>
        p.patient_email.toLowerCase().includes(term)
      );
    }

    if (filterStatus !== 'ALL') {
      result = result.filter((p) => p.status === filterStatus);
    }

    return result;
  }, [payments, searchTerm, filterStatus]);

  const paginatedPayments = useMemo(() => {
    const startIdx = (currentPage - 1) * pageSize;
    return filteredPayments.slice(startIdx, startIdx + pageSize);
  }, [filteredPayments, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredPayments.length / pageSize);

  const totalAmount = useMemo(
    () => payments.reduce((sum, p) => sum + p.amount, 0),
    [payments]
  );

  const paidAmount = useMemo(
    () => payments.filter((p) => p.status === 'PAID').reduce((sum, p) => sum + p.amount, 0),
    [payments]
  );

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">All Payments</h1>
          <p className="mt-2 text-gray-600">View and track all payment transactions</p>
        </div>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 p-4">
            <p className="text-sm text-gray-700">Total Transactions</p>
            <p className="mt-1 text-3xl font-bold text-blue-900">{payments.length}</p>
          </div>
          <div className="rounded-lg bg-gradient-to-br from-green-50 to-green-100 p-4">
            <p className="text-sm text-gray-700">Total Amount</p>
            <p className="mt-1 text-3xl font-bold text-green-900">₹{(totalAmount / 1000).toFixed(1)}k</p>
          </div>
          <div className="rounded-lg bg-gradient-to-br from-emerald-50 to-emerald-100 p-4">
            <p className="text-sm text-gray-700">Paid Amount</p>
            <p className="mt-1 text-3xl font-bold text-emerald-900">₹{(paidAmount / 1000).toFixed(1)}k</p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex gap-4 rounded-lg bg-white p-4 shadow-sm">
          <input
            type="text"
            placeholder="Search by patient email..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Status</option>
            <option value="PENDING">Pending</option>
            <option value="PAID">Paid</option>
            <option value="FAILED">Failed</option>
            <option value="REFUNDED">Refunded</option>
            <option value="OVERDUE">Overdue</option>
          </select>
        </div>

        {/* Payments Table */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading payments...</div>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
        ) : filteredPayments.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">
            No payments found.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="w-full">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Patient</th>
                  <th className="px-6 py-3 text-right text-sm font-semibold text-gray-700">Amount</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedPayments.map((payment) => (
                  <tr key={payment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-700">{payment.patient_email}</td>
                    <td className="px-6 py-4 text-right font-medium text-gray-900">₹{payment.amount}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${statusColors[payment.status]}`}>
                        {payment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {new Date(payment.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between rounded-lg bg-white p-4 shadow-sm">
            <div className="text-sm text-gray-600">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filteredPayments.length)} of{' '}
              {filteredPayments.length} payments
            </div>
            <div className="flex gap-2">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`rounded px-2 py-1 text-sm ${
                      currentPage === page
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
