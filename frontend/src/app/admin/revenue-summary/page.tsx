'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { extractApiErrorMessage } from '@/lib/error-utils';
import toast from 'react-hot-toast';


interface RevenueSummaryApiResponse {
  total_revenue: number;
  total_transactions: number;
  total_refunded_amount: number;
  pending_refund_count: number;
  net_revenue: number;
  revenue_by_payment_type: Array<{
    payment_type: string;
    total: number;
    count: number;
  }>;
}

export default function RevenueSummaryPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RevenueSummaryApiResponse | null>(null);

  useEffect(() => {
    const loadSummary = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<RevenueSummaryApiResponse>('/payments/revenue/');
        setSummary(response);
        setError(null);
      } catch (err) {
        const message = extractApiErrorMessage(err, 'Failed to load revenue summary');
        setError(message);
        toast.error(message);
      } finally {
        setIsLoading(false);
      }
    };

    loadSummary();
  }, []);

  const paidCount = useMemo(() => {
    if (!summary) return 0;
    return summary.revenue_by_payment_type.reduce((acc, item) => acc + (item.count || 0), 0);
  }, [summary]);

  const averageTransaction = useMemo(() => {
    if (!summary || summary.total_transactions === 0) return 0;
    return summary.total_revenue / summary.total_transactions;
  }, [summary]);

  const refundRate = useMemo(() => {
    if (!summary || summary.total_revenue === 0) return 0;
    return (summary.total_refunded_amount / summary.total_revenue) * 100;
  }, [summary]);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center text-gray-600">Loading revenue summary...</div>
      </MainLayout>
    );
  }

  if (error || !summary) {
    return (
      <MainLayout>
        <div className="space-y-6 p-6">
          <h1 className="text-3xl font-bold text-gray-900">Revenue Summary</h1>
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error || 'Unable to load revenue summary.'}</div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Revenue Summary</h1>
          <p className="mt-2 text-gray-600">Monthly financial overview and analytics</p>
        </div>

        {/* Main Metrics */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <div className="rounded-lg bg-gradient-to-br from-emerald-50 to-emerald-100 p-6">
            <p className="text-sm text-gray-700">Total Revenue</p>
            <p className="mt-2 text-4xl font-bold text-emerald-900">₹{(summary.total_revenue / 100000).toFixed(1)}L</p>
            <p className="mt-2 text-xs text-emerald-700">Net: ₹{(summary.net_revenue / 100000).toFixed(1)}L</p>
          </div>

          <div className="rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 p-6">
            <p className="text-sm text-gray-700">Transactions</p>
            <p className="mt-2 text-4xl font-bold text-blue-900">{summary.total_transactions}</p>
            <p className="mt-2 text-xs text-blue-700">Completed paid transactions</p>
          </div>

          <div className="rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 p-6">
            <p className="text-sm text-gray-700">Refunded Amount</p>
            <p className="mt-2 text-4xl font-bold text-orange-900">₹{(summary.total_refunded_amount / 1000).toFixed(0)}k</p>
            <p className="mt-2 text-xs text-orange-700">{summary.pending_refund_count} pending</p>
          </div>
        </div>

        {/* Transaction Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Paid Transactions</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">{paidCount}</p>
            <p className="mt-2 text-xs text-green-600">✓ Successful</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Pending Refunds</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">{summary.pending_refund_count}</p>
            <p className="mt-2 text-xs text-yellow-600">⏱️ Review required</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Refund Rate</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">{refundRate.toFixed(1)}%</p>
            <p className="mt-2 text-xs text-red-600">⚠️ Of gross revenue</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Avg Transaction</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">₹{averageTransaction.toLocaleString()}</p>
            <p className="mt-2 text-xs text-blue-600">📊 Per paid transaction</p>
          </div>
        </div>

        {/* Average Transaction */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="font-semibold text-gray-900">Key Insights</h2>
          <div className="mt-4 space-y-3 text-sm text-gray-700">
            <p>
              💰 <strong>Average Transaction:</strong> ₹{averageTransaction.toLocaleString()}
            </p>
            <p>
              💸 <strong>Total Refunded:</strong> ₹{summary.total_refunded_amount.toLocaleString()}
            </p>
            <p>
              ⚠️ <strong>Pending Refund Queue:</strong> {summary.pending_refund_count} requests
            </p>
            <p>
              ✓ <strong>Net Revenue:</strong> ₹{summary.net_revenue.toLocaleString()}
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-2">
          <Link
            href="/billing"
            className="flex items-center justify-between rounded-lg border border-blue-300 bg-blue-50 p-4 text-blue-700 hover:bg-blue-100"
          >
            <span className="font-medium">View Billing Details</span>
            <span>→</span>
          </Link>
          <Link
            href="/payments"
            className="flex items-center justify-between rounded-lg border border-green-300 bg-green-50 p-4 text-green-700 hover:bg-green-100"
          >
            <span className="font-medium">All Payments</span>
            <span>→</span>
          </Link>
        </div>
      </div>
    </MainLayout>
  );
}
