/**
 * Financial Reconciliation Reports - Phase 7
 * Path: frontend/src/pages/finance/reconciliation.tsx
 * Features: Daily/monthly reports, aging analysis, provider performance
 */

import { useEffect, useState } from 'react';
import axios from 'axios';

interface ReconciliationData {
  daily?: any;
  monthly?: any;
  receivables?: any;
  claims?: any;
  providers?: any[];
  refunds?: any;
}

export default function ReconciliationReports() {
  const [activeTab, setActiveTab] = useState('daily');
  const [data, setData] = useState<ReconciliationData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedMonth, setSelectedMonth] = useState(`${new Date().getFullYear()}-${String(new Date().getMonth() + 1).padStart(2, '0')}`);

  useEffect(() => {
    fetchReports();
  }, [activeTab, selectedDate, selectedMonth]);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      let newData: ReconciliationData = {};

      switch (activeTab) {
        case 'daily':
          const dailyRes = await axios.get(
            `${process.env.NEXT_PUBLIC_API_URL}/finance/reconciliation/daily/?date=${selectedDate}`,
            { headers }
          );
          newData.daily = dailyRes.data;
          break;

        case 'monthly':
          const [year, month] = selectedMonth.split('-');
          const monthlyRes = await axios.get(
            `${process.env.NEXT_PUBLIC_API_URL}/finance/reconciliation/monthly/?year=${year}&month=${month}`,
            { headers }
          );
          newData.monthly = monthlyRes.data;
          break;

        case 'receivables':
          const receivablesRes = await axios.get(
            `${process.env.NEXT_PUBLIC_API_URL}/finance/reconciliation/receivables/`,
            { headers }
          );
          newData.receivables = receivablesRes.data;
          break;

        case 'claims':
          const claimsRes = await axios.get(
            `${process.env.NEXT_PUBLIC_API_URL}/finance/reconciliation/claims/`,
            { headers }
          );
          newData.claims = claimsRes.data;
          break;

        case 'providers':
          const providersRes = await axios.get(
            `${process.env.NEXT_PUBLIC_API_URL}/finance/reconciliation/provider-performance/`,
            { headers }
          );
          newData.providers = providersRes.data;
          break;

        case 'refunds':
          const refundsRes = await axios.get(
            `${process.env.NEXT_PUBLIC_API_URL}/finance/reconciliation/refunds/`,
            { headers }
          );
          newData.refunds = refundsRes.data;
          break;
      }

      setData(newData);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  };

  const DailyReport = ({ daily }: any) => (
    <div className="space-y-6">
      <div className="flex gap-2 mb-6">
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Invoices Issued</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Count</span>
              <span className="font-semibold">{daily?.invoices_issued?.count || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Amount</span>
              <span className="font-semibold">Rs.{(daily?.invoices_issued?.total_amount || 0).toLocaleString()}</span>
            </div>
            <div className="border-t pt-3 flex justify-between">
              <span className="text-gray-600">Insurance Portion</span>
              <span className="text-blue-600 font-semibold">Rs.{(daily?.invoices_issued?.insurance_portion || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Patient Portion</span>
              <span className="text-green-600 font-semibold">Rs.{(daily?.invoices_issued?.patient_portion || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Payments Received</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Count</span>
              <span className="font-semibold">{daily?.payments_received?.count || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Amount</span>
              <span className="text-green-600 font-semibold">Rs.{(daily?.payments_received?.total_amount || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Claims Submitted</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Count</span>
              <span className="font-semibold">{daily?.claims_submitted?.count || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Amount</span>
              <span className="font-semibold">Rs.{(daily?.claims_submitted?.total_amount || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Refunds Processed</h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Count</span>
              <span className="font-semibold">{daily?.refunds_processed?.count || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Total Amount</span>
              <span className="text-red-600 font-semibold">Rs.{(daily?.refunds_processed?.total_amount || 0).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const MonthlyReport = ({ monthly }: any) => (
    <div className="space-y-6">
      <div className="flex gap-2 mb-6">
        <input
          type="month"
          value={selectedMonth}
          onChange={(e) => setSelectedMonth(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <p className="text-blue-700 font-semibold text-sm">Total Invoiced</p>
          <p className="text-2xl font-bold text-blue-900 mt-2">Rs.{(monthly?.total_invoiced || 0).toLocaleString()}</p>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <p className="text-green-700 font-semibold text-sm">Total Collected</p>
          <p className="text-2xl font-bold text-green-900 mt-2">Rs.{(monthly?.total_collected || 0).toLocaleString()}</p>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
          <p className="text-purple-700 font-semibold text-sm">Collection %</p>
          <p className="text-2xl font-bold text-purple-900 mt-2">{monthly?.collection_percentage?.toFixed(1)}%</p>
        </div>

        <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
          <p className="text-orange-700 font-semibold text-sm">Total Claimed</p>
          <p className="text-2xl font-bold text-orange-900 mt-2">Rs.{(monthly?.total_claimed || 0).toLocaleString()}</p>
        </div>

        <div className="bg-teal-50 border border-teal-200 rounded-lg p-6">
          <p className="text-teal-700 font-semibold text-sm">Total Approved</p>
          <p className="text-2xl font-bold text-teal-900 mt-2">Rs.{(monthly?.total_approved || 0).toLocaleString()}</p>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-700 font-semibold text-sm">Denial Rate</p>
          <p className="text-2xl font-bold text-red-900 mt-2">{monthly?.denial_percentage?.toFixed(1)}%</p>
        </div>
      </div>

      {monthly?.by_provider && monthly.by_provider.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-4">By Insurance Provider</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-2 text-left">Provider</th>
                  <th className="px-4 py-2 text-right">Invoices</th>
                  <th className="px-4 py-2 text-right">Total Amount</th>
                </tr>
              </thead>
              <tbody>
                {monthly.by_provider.map((p: any, idx: number) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-2">{p.provider}</td>
                    <td className="px-4 py-2 text-right">{p.invoice_count}</td>
                    <td className="px-4 py-2 text-right font-semibold">Rs.{(p.total_amount || 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );

  const ReceivablesReport = ({ receivables }: any) => (
    <div className="space-y-6">
      <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
        <p className="text-red-700 font-semibold">Outstanding Receivables</p>
        <p className="text-3xl font-bold text-red-900 mt-2">Rs.{(receivables?.total_outstanding || 0).toLocaleString()}</p>
        <p className="text-red-600 text-sm mt-2">{receivables?.invoice_count} invoices pending</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Aging Buckets</h3>
        <div className="space-y-3">
          {[
            { key: 'current', label: 'Current (Not Yet Due)', color: 'bg-green-100 text-green-700' },
            { key: '30_60_days', label: '30-60 Days Overdue', color: 'bg-yellow-100 text-yellow-700' },
            { key: '60_90_days', label: '60-90 Days Overdue', color: 'bg-orange-100 text-orange-700' },
            { key: 'over_90_days', label: 'Over 90 Days Overdue', color: 'bg-red-100 text-red-700' },
          ].map((bucket) => (
            <div key={bucket.key} className={`${bucket.color} p-4 rounded-lg flex justify-between`}>
              <span className="font-semibold">{bucket.label}</span>
              <span className="font-bold">Rs.{(receivables?.aging_buckets?.[bucket.key] || 0).toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const ClaimsReport = ({ claims }: any) => (
    <div className="space-y-6">
      {claims?.avg_pending_days && (
        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 mb-6">
          <p className="text-blue-700 font-semibold">Average Days Pending</p>
          <p className="text-3xl font-bold text-blue-900 mt-2">{claims.avg_pending_days} days</p>
          <p className="text-blue-600 text-sm mt-2">{claims?.total_pending} claims currently pending</p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold">Status</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Count</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Total Claimed</th>
              <th className="px-6 py-3 text-right text-sm font-semibold">Total Approved</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {claims?.by_status?.map((s: any, idx: number) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-6 py-3 font-semibold text-gray-900">{s.status}</td>
                <td className="px-6 py-3 text-right">{s.count}</td>
                <td className="px-6 py-3 text-right">Rs.{(s.total_claimed || 0).toLocaleString()}</td>
                <td className="px-6 py-3 text-right text-green-600 font-semibold">Rs.{(s.total_approved || 0).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const ProvidersReport = ({ providers }: any) => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-6 py-3 text-left font-semibold">Provider</th>
              <th className="px-6 py-3 text-right font-semibold">Policies</th>
              <th className="px-6 py-3 text-right font-semibold">Claims</th>
              <th className="px-6 py-3 text-right font-semibold">Approved</th>
              <th className="px-6 py-3 text-right font-semibold">Denied</th>
              <th className="px-6 py-3 text-right font-semibold">Approval %</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {providers?.map((p: any, idx: number) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-6 py-3 font-semibold">{p.provider}</td>
                <td className="px-6 py-3 text-right">{p.policy_count}</td>
                <td className="px-6 py-3 text-right">{p.total_claims}</td>
                <td className="px-6 py-3 text-right text-green-600">{p.approved_claims}</td>
                <td className="px-6 py-3 text-right text-red-600">{p.denied_claims}</td>
                <td className="px-6 py-3 text-right">
                  <span className={`font-semibold ${p.approval_rate >= 80 ? 'text-green-600' : p.approval_rate >= 60 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {p.approval_rate}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const RefundsReport = ({ refunds }: any) => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <p className="text-yellow-700 font-semibold text-sm">Pending Approval</p>
          <p className="text-2xl font-bold text-yellow-900 mt-2">Rs.{(refunds?.pending_approval || 0).toLocaleString()}</p>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <p className="text-green-700 font-semibold text-sm">Total Refunded</p>
          <p className="text-2xl font-bold text-green-900 mt-2">Rs.{(refunds?.total_refunded || 0).toLocaleString()}</p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="font-semibold text-gray-900 mb-4">By Status</h3>
        <div className="space-y-2">
          {refunds?.by_status?.map((s: any, idx: number) => (
            <div key={idx} className="flex justify-between p-3 bg-gray-50 rounded">
              <span className="font-semibold text-gray-900">{s.status}</span>
              <div className="flex gap-6">
                <span className="text-gray-600">{s.count} refunds</span>
                <span className="font-semibold">Rs.{(s.total_amount || 0).toLocaleString()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  if (loading) return <div className="p-8 text-center">Loading report...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Financial Reconciliation Reports</h1>
          <p className="text-gray-600">Detailed analysis of invoices, claims, receivables, and refunds</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">{error}</div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-gray-300">
          {[
            { id: 'daily', label: 'Daily Reconciliation' },
            { id: 'monthly', label: 'Monthly Report' },
            { id: 'receivables', label: 'Outstanding Receivables' },
            { id: 'claims', label: 'Claims Status' },
            { id: 'providers', label: 'Provider Performance' },
            { id: 'refunds', label: 'Refund Summary' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 font-semibold text-sm ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Reports */}
        <div className="bg-white rounded-lg p-6">
          {activeTab === 'daily' && <DailyReport daily={data.daily} />}
          {activeTab === 'monthly' && <MonthlyReport monthly={data.monthly} />}
          {activeTab === 'receivables' && <ReceivablesReport receivables={data.receivables} />}
          {activeTab === 'claims' && <ClaimsReport claims={data.claims} />}
          {activeTab === 'providers' && <ProvidersReport providers={data.providers} />}
          {activeTab === 'refunds' && <RefundsReport refunds={data.refunds} />}
        </div>
      </div>
    </div>
  );
}
