'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';


interface RevenueSummary {
  total_revenue: number;
  gross_revenue: number;
  refunded_amount: number;
  pending_refunds: number;
  paid_count: number;
  unpaid_count: number;
  overdue_count: number;
  average_transaction: number;
  success_rate: number;
}

export default function RevenueSummaryPage() {
  const [userRole] = useState(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('userRole') || '').toUpperCase();
    }
    return '';
  });
  const [summary] = useState<RevenueSummary>({
    total_revenue: 1485000,
    gross_revenue: 1550000,
    refunded_amount: 65000,
    pending_refunds: 12,
    paid_count: 198,
    unpaid_count: 32,
    overdue_count: 15,
    average_transaction: 7500,
    success_rate: 86.1,
  });

  const isAdminOpsRole = userRole === 'ADMIN' || userRole === 'RECEPTIONIST';

  if (!isAdminOpsRole) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
              Back to Dashboard
            </Link>
          </div>
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
            <p className="mt-2 text-xs text-emerald-700">↑ 12% from last month</p>
          </div>

          <div className="rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 p-6">
            <p className="text-sm text-gray-700">Gross Revenue</p>
            <p className="mt-2 text-4xl font-bold text-blue-900">₹{(summary.gross_revenue / 100000).toFixed(1)}L</p>
            <p className="mt-2 text-xs text-blue-700">Before refunds</p>
          </div>

          <div className="rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 p-6">
            <p className="text-sm text-gray-700">Refunded Amount</p>
            <p className="mt-2 text-4xl font-bold text-orange-900">₹{(summary.refunded_amount / 1000).toFixed(0)}k</p>
            <p className="mt-2 text-xs text-orange-700">{summary.pending_refunds} pending</p>
          </div>
        </div>

        {/* Transaction Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Paid Transactions</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">{summary.paid_count}</p>
            <p className="mt-2 text-xs text-green-600">✓ Successful</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Unpaid Invoices</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">{summary.unpaid_count}</p>
            <p className="mt-2 text-xs text-yellow-600">⏱️ Pending</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Overdue Payments</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">{summary.overdue_count}</p>
            <p className="mt-2 text-xs text-red-600">⚠️ Action needed</p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-xs text-gray-600">Success Rate</p>
            <p className="mt-2 text-2xl font-bold text-gray-900">{summary.success_rate}%</p>
            <p className="mt-2 text-xs text-blue-600">📊 Transaction rate</p>
          </div>
        </div>

        {/* Average Transaction */}
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="font-semibold text-gray-900">Key Insights</h2>
          <div className="mt-4 space-y-3 text-sm text-gray-700">
            <p>
              💰 <strong>Average Transaction:</strong> ₹{summary.average_transaction.toLocaleString()}
            </p>
            <p>
              📈 <strong>Monthly Growth:</strong> 12% increase in total revenue
            </p>
            <p>
              ⚠️ <strong>Alert:</strong> {summary.overdue_count} overdue payments totaling ~₹{(summary.overdue_count * summary.average_transaction / 1000).toFixed(0)}k
            </p>
            <p>
              ✓ <strong>Payment Success Rate:</strong> {summary.success_rate}% of all transactions succeeded
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
