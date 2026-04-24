import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/Auth';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

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

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-NP', {
    maximumFractionDigits: 0,
  }).format(value || 0);

export default function FinanceDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await apiClient.get<DashboardStats>('/finance/dashboard/');
        setStats(response);
      } catch (err: any) {
        setError(err?.message || 'Failed to load finance dashboard');
      } finally {
        setLoading(false);
      }
    };

    void fetchDashboard();
  }, []);

  const topStatuses = useMemo(
    () => [...(stats?.claims_summary.by_status || [])].sort((a, b) => b.count - a.count),
    [stats]
  );

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.finance}
      title="finance dashboard"
      description="Finance dashboards are restricted to finance and insurance roles."
    >
      <PageHeader
        title="Finance Command Center"
        description="Claims, collections, denial exposure, and reconciliation signals in one secured workspace."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/finance/invoices" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
              Invoices
            </Link>
            <Link href="/finance/claims" className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">
              Claims
            </Link>
          </div>
        }
      />

      {loading ? <EmptyState title="Loading finance dashboard" description="Pulling the latest finance and claims metrics." /> : null}
      {!loading && error ? <EmptyState title="Finance dashboard unavailable" description={error} /> : null}

      {!loading && !error && stats ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Total Claims" value={stats.claims_summary.total_claims} tone="blue" />
            <StatCard label="Collection Rate" value={`${stats.invoice_summary.collection_rate.toFixed(1)}%`} tone="green" />
            <StatCard label="Denial Rate" value={`${stats.claims_summary.denial_rate.toFixed(1)}%`} tone="red" />
            <StatCard label="Pending Reworks" value={stats.pending_reworks} tone="amber" />
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
            <SectionCard title="Claim Status Mix" subtitle="Current insurance claim distribution and value by status.">
              {topStatuses.length === 0 ? (
                <EmptyState title="No claim activity yet" description="Status metrics will appear after claim submissions sync." />
              ) : (
                <div className="space-y-3">
                  {topStatuses.map((item) => (
                    <div key={item.status} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 px-4 py-3">
                      <div className="flex items-center gap-2">
                        <StatusBadge value={item.status.replaceAll('_', ' ')} />
                        <span className="text-sm text-gray-600">{item.count} claims</span>
                      </div>
                      <span className="text-sm font-semibold text-gray-900">Rs. {formatCurrency(item.total_amount)}</span>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Aging Watchlist" subtitle="Claims requiring immediate follow-up to protect cash flow.">
              <div className="grid gap-4">
                <StatCard label="Over 30 Days" value={stats.aging_analysis.claims_over_30_days} tone="amber" />
                <StatCard label="Over 45 Days" value={stats.aging_analysis.claims_over_45_days} tone="red" />
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                  Prioritize denials and older claims first to reduce preventable aging.
                </div>
              </div>
            </SectionCard>
          </div>

          <SectionCard title="Invoice Performance" subtitle="Collection and receivables snapshot from the current ledger.">
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <StatCard label="Total Invoiced" value={`Rs. ${formatCurrency(stats.invoice_summary.total_invoiced)}`} />
              <StatCard label="Collected" value={`Rs. ${formatCurrency(stats.invoice_summary.total_collected)}`} tone="green" />
              <StatCard label="Pending Invoices" value={stats.invoice_summary.pending_invoices} tone="amber" />
              <StatCard label="Collection Rate" value={`${stats.invoice_summary.collection_rate.toFixed(1)}%`} tone="blue" />
            </div>
          </SectionCard>

          <SectionCard title="Quick Actions" subtitle="Jump directly into the highest-risk finance workflows.">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              {[
                { href: '/finance/invoices', label: 'Manage Invoices', detail: 'Finalize, track, and follow up on billing.', tone: 'bg-blue-600 hover:bg-blue-700' },
                { href: '/finance/claims', label: 'Insurance Claims', detail: 'Review submission status and aging.', tone: 'bg-emerald-600 hover:bg-emerald-700' },
                { href: '/finance/denials', label: 'Denial Reworks', detail: 'Resolve reworks and resubmissions quickly.', tone: 'bg-amber-600 hover:bg-amber-700' },
                { href: '/finance/reconciliation', label: 'Reconciliation', detail: 'Inspect receivables, refunds, and provider trends.', tone: 'bg-violet-600 hover:bg-violet-700' },
                { href: '/compliance', label: 'Compliance Center', detail: 'Cross-check incidents and operational risks.', tone: 'bg-slate-900 hover:bg-slate-800' },
              ].map((action) => (
                <Link key={action.href} href={action.href} className={`rounded-lg px-4 py-4 text-white ${action.tone}`}>
                  <p className="font-semibold">{action.label}</p>
                  <p className="mt-1 text-sm text-white/80">{action.detail}</p>
                </Link>
              ))}
            </div>
          </SectionCard>
        </>
      ) : null}
    </ProtectedPage>
  );
}
