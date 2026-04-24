import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/Auth';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface Claim {
  id: number;
  claim_number: string;
  patient_name: string;
  insurance_provider: string;
  claimed_amount: number;
  approved_amount: number | null;
  status: string;
  days_pending: number;
}

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    const fetchClaims = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await apiClient.get<{ results?: Claim[] }>('/claims/', {
          params: filterStatus ? { status: filterStatus } : {},
        });
        setClaims(response.results || []);
      } catch (err: any) {
        setError(err?.message || 'Failed to load claims');
      } finally {
        setLoading(false);
      }
    };

    void fetchClaims();
  }, [filterStatus]);

  const summary = useMemo(
    () => ({
      needsAction: claims.filter((claim) => ['REJECTED', 'DENIED', 'REWORK_NEEDED', 'PENDING_MORE_INFO'].includes(claim.status)).length,
      inProgress: claims.filter((claim) => ['SUBMITTED', 'PROCESSING'].includes(claim.status)).length,
      approved: claims.filter((claim) => ['APPROVED', 'APPROVED_WITH_REDUCTION'].includes(claim.status)).length,
      total: claims.length,
    }),
    [claims]
  );

  const sortedClaims = useMemo(() => {
    const priority: Record<string, number> = {
      PENDING_MORE_INFO: 1,
      REWORK_NEEDED: 2,
      DENIED: 3,
      REJECTED: 4,
      PROCESSING: 5,
      SUBMITTED: 6,
      APPROVED_WITH_REDUCTION: 7,
      APPROVED: 8,
      DRAFT: 9,
    };

    return [...claims].sort((a, b) => (priority[a.status] || 99) - (priority[b.status] || 99));
  }, [claims]);

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.finance}
      title="insurance claims"
      description="Insurance claim workflows are restricted to finance and insurance roles."
    >
      <PageHeader
        title="Insurance Claims"
        description="Track insurer submissions, approvals, and aging risks from the shared finance workspace."
        actions={
          <Link href="/finance/dashboard" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
            Back to Dashboard
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Needs Action" value={summary.needsAction} tone="red" />
        <StatCard label="In Progress" value={summary.inProgress} tone="amber" />
        <StatCard label="Approved" value={summary.approved} tone="green" />
        <StatCard label="Total Claims" value={summary.total} tone="blue" />
      </div>

      <SectionCard title="Claim Queue" subtitle="Filter and review claims before denials turn into aging exposure.">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <select
            value={filterStatus}
            onChange={(event) => setFilterStatus(event.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="PROCESSING">Processing</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="DENIED">Denied</option>
            <option value="REWORK_NEEDED">Rework Needed</option>
          </select>
        </div>

        {loading ? <EmptyState title="Loading claims" description="Refreshing claim status and aging data." /> : null}
        {!loading && error ? <EmptyState title="Claims unavailable" description={error} /> : null}
        {!loading && !error && sortedClaims.length === 0 ? <EmptyState title="No claims found" description="Adjust the filter or create a new claim to start the workflow." /> : null}

        {!loading && !error && sortedClaims.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Claim</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Patient</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Insurer</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Claimed</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Approved</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Aging</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sortedClaims.map((claim) => (
                  <tr key={claim.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold text-gray-900">{claim.claim_number}</td>
                    <td className="px-4 py-3 text-gray-700">{claim.patient_name}</td>
                    <td className="px-4 py-3 text-gray-700">{claim.insurance_provider}</td>
                    <td className="px-4 py-3 text-right text-gray-900">Rs. {claim.claimed_amount.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right text-gray-900">
                      {claim.approved_amount ? `Rs. ${claim.approved_amount.toLocaleString()}` : 'Pending'}
                    </td>
                    <td className="px-4 py-3"><StatusBadge value={claim.status.replaceAll('_', ' ')} /></td>
                    <td className="px-4 py-3 text-gray-700">{claim.days_pending > 0 ? `${claim.days_pending} days` : 'Fresh'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </SectionCard>
    </ProtectedPage>
  );
}
