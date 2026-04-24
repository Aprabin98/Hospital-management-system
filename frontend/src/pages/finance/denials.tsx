import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/Auth';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface DenialRework {
  id: number;
  claim_number: string;
  patient_name: string;
  original_denial_reason: string;
  status: string;
  assigned_to_name: string | null;
  correction_notes: string;
}

export default function DenialReworksPage() {
  const { userRole } = useAuth();
  const [reworks, setReworks] = useState<DenialRework[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('PENDING_REVIEW');

  useEffect(() => {
    const fetchReworks = async () => {
      try {
        setLoading(true);
        setError('');

        const params =
          filterStatus && filterStatus !== 'PENDING'
            ? { status: filterStatus }
            : {};
        const path =
          filterStatus === 'PENDING'
            ? '/denial-reworks/pending/'
            : '/denial-reworks/';

        const response = await apiClient.get<{ results?: DenialRework[] }>(path, { params });
        setReworks(response.results || []);
      } catch (err: any) {
        setError(err?.message || 'Failed to load denial reworks');
      } finally {
        setLoading(false);
      }
    };

    void fetchReworks();
  }, [filterStatus]);

  const summary = useMemo(
    () => ({
      pending: reworks.filter((item) => item.status === 'PENDING_REVIEW').length,
      correction: reworks.filter((item) => item.status === 'UNDER_CORRECTION').length,
      total: reworks.length,
    }),
    [reworks]
  );

  const role = (userRole || '').toUpperCase();
  const canAssign = role === 'ADMIN' || role === 'INSURANCE_COORDINATOR';
  const canResubmit = role === 'ADMIN' || role === 'BILLING_OFFICER';

  const handleAssign = async (reworkId: number) => {
    if (!canAssign) return;

    const billingOfficerId = window.prompt('Enter billing officer ID for assignment');
    if (!billingOfficerId) return;

    try {
      await apiClient.post(`/denial-reworks/${reworkId}/assign/`, {
        assigned_to_id: billingOfficerId,
      });
      setReworks((current) =>
        current.map((item) =>
          item.id === reworkId
            ? { ...item, status: 'UNDER_CORRECTION' }
            : item
        )
      );
    } catch (err: any) {
      setError(err?.message || 'Failed to assign rework');
    }
  };

  const handleResubmit = async (reworkId: number) => {
    if (!canResubmit) return;

    const correctionNotes = window.prompt('Enter correction notes for resubmission');
    if (!correctionNotes) return;

    try {
      await apiClient.post(`/denial-reworks/${reworkId}/resubmit/`, {
        correction_notes: correctionNotes,
        submission_notes: correctionNotes,
      });
      setReworks((current) =>
        current.map((item) =>
          item.id === reworkId
            ? { ...item, status: 'RESUBMITTED', correction_notes: correctionNotes }
            : item
        )
      );
    } catch (err: any) {
      setError(err?.message || 'Failed to resubmit denial');
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.finance}
      title="denial reworks"
      description="Denial reworks are restricted to finance and insurance roles."
    >
      <PageHeader
        title="Denial Rework Queue"
        description="Prioritize denied claims, route assignments, and resubmit corrections from one secure queue."
      />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Pending Review" value={summary.pending} tone="red" />
        <StatCard label="Under Correction" value={summary.correction} tone="amber" />
        <StatCard label="Total Reworks" value={summary.total} tone="blue" />
      </div>

      <SectionCard title="Rework Queue" subtitle="Focus the queue by rework state and take the next safe action.">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <select
            value={filterStatus}
            onChange={(event) => setFilterStatus(event.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm"
          >
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="UNDER_CORRECTION">Under Correction</option>
            <option value="RESUBMITTED">Resubmitted</option>
            <option value="RESOLVED">Resolved</option>
            <option value="ABANDONED">Abandoned</option>
          </select>
        </div>

        {loading ? <EmptyState title="Loading denial queue" description="Refreshing denial assignments and rework status." /> : null}
        {!loading && error ? <EmptyState title="Denial queue unavailable" description={error} /> : null}
        {!loading && !error && reworks.length === 0 ? <EmptyState title="No denial reworks found" description="The selected filter currently has no records." /> : null}

        {!loading && !error && reworks.length > 0 ? (
          <div className="space-y-3">
            {reworks.map((rework) => (
              <div key={rework.id} className="rounded-lg border border-gray-200 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-gray-900">{rework.claim_number}</p>
                      <StatusBadge value={rework.status.replaceAll('_', ' ')} />
                    </div>
                    <p className="text-sm text-gray-700">{rework.patient_name}</p>
                    <p className="text-sm text-gray-600">{rework.original_denial_reason}</p>
                    <p className="text-xs text-gray-500">
                      Assigned to: {rework.assigned_to_name || 'Unassigned'}
                    </p>
                    {rework.correction_notes ? (
                      <p className="text-xs text-gray-500">Latest notes: {rework.correction_notes}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {rework.status === 'PENDING_REVIEW' ? (
                      <button
                        type="button"
                        disabled={!canAssign}
                        onClick={() => handleAssign(rework.id)}
                        className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-700 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Assign
                      </button>
                    ) : null}
                    {rework.status === 'UNDER_CORRECTION' ? (
                      <button
                        type="button"
                        disabled={!canResubmit}
                        onClick={() => handleResubmit(rework.id)}
                        className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Resubmit
                      </button>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </SectionCard>
    </ProtectedPage>
  );
}
