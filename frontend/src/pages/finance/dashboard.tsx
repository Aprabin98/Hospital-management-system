/**
 * Finance Dashboard - Phase 7 Implementation
 * Path: frontend/src/pages/finance/dashboard.tsx
 * Access: BILLING_OFFICER, INSURANCE_COORDINATOR, ADMIN
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import Link from 'next/link';

interface DashboardStats {
  claims_summary: {
    total_claims: number;
    by_status: Array<{ status: string; count: number; total_amount: number }>;
    denial_rate: number;
  };
  invoice_summary: {
    total_invoiced: number;
    total_collected: number;
    collection_rate: number;
    pending_invoices: number;
  };
  aging_analysis: {
    claims_over_30_days: number;
    claims_over_45_days: number;
  };
  pending_reworks: number;
}

export default function FinanceDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const token = localStorage.getItem('token');
        const userRole = localStorage.getItem('userRole');

        if (!['BILLING_OFFICER', 'INSURANCE_COORDINATOR', 'ADMIN'].includes(userRole || '')) {
          router.push('/');
          return;
        }

        const response = await axios.get(
          `${process.env.NEXT_PUBLIC_API_URL}/finance/dashboard/`,
          { headers: { Authorization: `Bearer ${token}` } }
        );

        setStats(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, [router]);

  if (loading) return <div className="p-8 text-center">Loading dashboard...</div>;
  if (error) return <div className="p-8 bg-red-50 text-red-700">{error}</div>;
  if (!stats) return null;

  const collectionRate = stats.invoice_summary.collection_rate.toFixed(1);
  const denialRate = stats.claims_summary.denial_rate.toFixed(1);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Finance Dashboard</h1>
          <p className="text-gray-600">Phase 7: Finance & Insurance Maturity</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Claims */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Claims</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  {stats.claims_summary.total_claims}
                </p>
              </div>
              <div className="text-4xl text-blue-100">📋</div>
            </div>
          </div>

          {/* Collection Rate */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Collection Rate</p>
                <p className="text-3xl font-bold text-green-600 mt-2">{collectionRate}%</p>
                <p className="text-xs text-gray-500 mt-1">
                  Rs.{(stats.invoice_summary.total_collected || 0).toLocaleString()}
                </p>
              </div>
              <div className="text-4xl text-green-100">💰</div>
            </div>
          </div>

          {/* Denial Rate */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Denial Rate</p>
                <p className="text-3xl font-bold text-red-600 mt-2">{denialRate}%</p>
              </div>
              <div className="text-4xl text-red-100">⚠️</div>
            </div>
          </div>

          {/* Pending Reworks */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Pending Reworks</p>
                <p className="text-3xl font-bold text-orange-600 mt-2">
                  {stats.pending_reworks}
                </p>
              </div>
              <div className="text-4xl text-orange-100">🔧</div>
            </div>
          </div>
        </div>

        {/* Claims Status Breakdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Claims by Status</h2>
            <div className="space-y-3">
              {stats.claims_summary.by_status.map((item: any) => (
                <div key={item.status} className="flex items-center justify-between py-2 border-b">
                  <span className="text-gray-700 capitalize">{item.status.replace(/_/g, ' ')}</span>
                  <div className="flex gap-4">
                    <span className="font-semibold text-gray-900">{item.count}</span>
                    <span className="text-gray-600">Rs.{(item.total_amount || 0).toLocaleString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Aging Analysis */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Claim Aging</h2>
            <div className="space-y-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
                <p className="text-yellow-800 font-semibold mb-2">⏰ Claims Over 30 Days</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {stats.aging_analysis.claims_over_30_days}
                </p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded p-4">
                <p className="text-red-800 font-semibold mb-2">🔴 Claims Over 45 Days</p>
                <p className="text-2xl font-bold text-red-600">
                  {stats.aging_analysis.claims_over_45_days}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Invoice Summary */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Invoice Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-gray-600 text-sm mb-2">Total Invoiced</p>
              <p className="text-3xl font-bold text-gray-900">
                Rs.{(stats.invoice_summary.total_invoiced || 0).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-gray-600 text-sm mb-2">Total Collected</p>
              <p className="text-3xl font-bold text-green-600">
                Rs.{(stats.invoice_summary.total_collected || 0).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-gray-600 text-sm mb-2">Pending Invoices</p>
              <p className="text-2xl font-bold text-orange-600">
                {stats.invoice_summary.pending_invoices}
              </p>
            </div>
            <div>
              <p className="text-gray-600 text-sm mb-2">Collection Rate</p>
              <p className="text-2xl font-bold text-blue-600">{collectionRate}%</p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Link
            href="/finance/invoices"
            className="bg-blue-600 text-white rounded-lg shadow p-6 hover:bg-blue-700 transition"
          >
            <p className="text-lg font-semibold mb-2">📄 Manage Invoices</p>
            <p className="text-blue-100 text-sm">Create and manage proforma & final invoices</p>
          </Link>

          <Link
            href="/finance/claims"
            className="bg-green-600 text-white rounded-lg shadow p-6 hover:bg-green-700 transition"
          >
            <p className="text-lg font-semibold mb-2">📋 Insurance Claims</p>
            <p className="text-green-100 text-sm">Submit and track insurance claims</p>
          </Link>

          <Link
            href="/finance/denials"
            className="bg-orange-600 text-white rounded-lg shadow p-6 hover:bg-orange-700 transition"
          >
            <p className="text-lg font-semibold mb-2">🔧 Denial Reworks</p>
            <p className="text-orange-100 text-sm">Manage rejected claims and corrections</p>
          </Link>

          <Link
            href="/finance/reconciliation"
            className="bg-purple-600 text-white rounded-lg shadow p-6 hover:bg-purple-700 transition"
          >
            <p className="text-lg font-semibold mb-2">📊 Reconciliation Reports</p>
            <p className="text-purple-100 text-sm">Daily/monthly reports and receivables analysis</p>
          </Link>

          <Link
            href="/compliance"
            className="bg-slate-800 text-white rounded-lg shadow p-6 hover:bg-slate-900 transition"
          >
            <p className="text-lg font-semibold mb-2">🛡️ Compliance Center</p>
            <p className="text-slate-200 text-sm">Incident tracking, SLA alerts, backups, and retention</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
