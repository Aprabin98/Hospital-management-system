import { useEffect, useState } from 'react';
import { ProtectedPage } from '@/components/Auth';
import { EmptyState, PageHeader, SectionCard, StatCard } from '@/components/UI';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

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
    const fetchReports = async () => {
      try {
        setLoading(true);
        setError('');
        let nextData: ReconciliationData = {};

        switch (activeTab) {
          case 'daily':
            nextData.daily = await apiClient.get('/finance/reconciliation/daily/', { params: { date: selectedDate } });
            break;
          case 'monthly': {
            const [year, month] = selectedMonth.split('-');
            nextData.monthly = await apiClient.get('/finance/reconciliation/monthly/', { params: { year, month } });
            break;
          }
          case 'receivables':
            nextData.receivables = await apiClient.get('/finance/reconciliation/receivables/');
            break;
          case 'claims':
            nextData.claims = await apiClient.get('/finance/reconciliation/claims/');
            break;
          case 'providers':
            nextData.providers = await apiClient.get('/finance/reconciliation/provider-performance/');
            break;
          case 'refunds':
            nextData.refunds = await apiClient.get('/finance/reconciliation/refunds/');
            break;
        }

        setData(nextData);
      } catch (err: any) {
        setError(err?.message || 'Failed to load reconciliation report');
      } finally {
        setLoading(false);
      }
    };

    void fetchReports();
  }, [activeTab, selectedDate, selectedMonth]);

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.finance}
      title="reconciliation reports"
      description="Reconciliation reports are restricted to finance and insurance roles."
    >
      <PageHeader
        title="Financial Reconciliation"
        description="Daily, monthly, receivables, provider, and refund reporting in the shared finance shell."
      />

      <div className="flex flex-wrap gap-2">
        {[
          ['daily', 'Daily'],
          ['monthly', 'Monthly'],
          ['receivables', 'Receivables'],
          ['claims', 'Claims'],
          ['providers', 'Providers'],
          ['refunds', 'Refunds'],
        ].map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setActiveTab(id)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold ${
              activeTab === id
                ? 'bg-slate-900 text-white'
                : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? <EmptyState title="Loading reconciliation report" description="Refreshing the selected finance reporting view." /> : null}
      {!loading && error ? <EmptyState title="Report unavailable" description={error} /> : null}

      {!loading && !error ? (
        <SectionCard title="Report Detail" subtitle="Operational reporting for finance review and follow-up.">
          {activeTab === 'daily' ? (
            <div className="space-y-4">
              <input type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm" />
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <StatCard label="Invoices Issued" value={data.daily?.invoices_issued?.count || 0} tone="blue" />
                <StatCard label="Payments Received" value={data.daily?.payments_received?.count || 0} tone="green" />
                <StatCard label="Claims Submitted" value={data.daily?.claims_submitted?.count || 0} tone="amber" />
                <StatCard label="Refunds Processed" value={data.daily?.refunds_processed?.count || 0} tone="red" />
              </div>
            </div>
          ) : null}

          {activeTab === 'monthly' ? (
            <div className="space-y-4">
              <input type="month" value={selectedMonth} onChange={(event) => setSelectedMonth(event.target.value)} className="rounded-lg border border-gray-300 px-4 py-2 text-sm" />
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                <StatCard label="Total Invoiced" value={`Rs. ${(data.monthly?.total_invoiced || 0).toLocaleString()}`} tone="blue" />
                <StatCard label="Total Collected" value={`Rs. ${(data.monthly?.total_collected || 0).toLocaleString()}`} tone="green" />
                <StatCard label="Denial Rate" value={`${data.monthly?.denial_percentage?.toFixed?.(1) || 0}%`} tone="red" />
              </div>
            </div>
          ) : null}

          {activeTab === 'receivables' ? (
            <div className="grid gap-4 md:grid-cols-2">
              <StatCard label="Outstanding Receivables" value={`Rs. ${(data.receivables?.total_outstanding || 0).toLocaleString()}`} tone="red" />
              <StatCard label="Pending Invoices" value={data.receivables?.invoice_count || 0} tone="amber" />
            </div>
          ) : null}

          {activeTab === 'claims' ? (
            <div className="grid gap-4 md:grid-cols-2">
              <StatCard label="Average Days Pending" value={data.claims?.avg_pending_days || 0} tone="amber" />
              <StatCard label="Pending Claims" value={data.claims?.total_pending || 0} tone="blue" />
            </div>
          ) : null}

          {activeTab === 'providers' ? (
            data.providers?.length ? (
              <div className="space-y-3">
                {data.providers.map((provider: any, index: number) => (
                  <div key={`${provider.provider}-${index}`} className="rounded-lg border border-gray-200 px-4 py-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="font-semibold text-gray-900">{provider.provider}</p>
                      <p className="text-sm text-gray-600">Approval rate: {provider.approval_rate}%</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No provider reporting yet" description="Provider performance appears after claims accumulate." />
            )
          ) : null}

          {activeTab === 'refunds' ? (
            <div className="grid gap-4 md:grid-cols-2">
              <StatCard label="Pending Approval" value={`Rs. ${(data.refunds?.pending_approval || 0).toLocaleString()}`} tone="amber" />
              <StatCard label="Total Refunded" value={`Rs. ${(data.refunds?.total_refunded || 0).toLocaleString()}`} tone="green" />
            </div>
          ) : null}
        </SectionCard>
      ) : null}
    </ProtectedPage>
  );
}
