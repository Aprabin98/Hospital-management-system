import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/Auth';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface PreAuth {
  id: number;
  patient_name: string;
  insurance_provider: string;
  treatment_code: string;
  estimated_amount: number;
  approved_amount: number | null;
  status: string;
  pre_auth_number: string | null;
  valid_until: string | null;
}

export default function PreAuthsPage() {
  const [preAuths, setPreAuths] = useState<PreAuth[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    treatment_code: '',
    estimated_amount: '',
    insurance_provider: '',
  });

  useEffect(() => {
    const fetchPreAuths = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await apiClient.get<{ results?: PreAuth[] }>('/pre-auths/', {
          params: filterStatus ? { status: filterStatus } : {},
        });
        setPreAuths(response.results || []);
      } catch (err: any) {
        setError(err?.message || 'Failed to load pre-authorizations');
      } finally {
        setLoading(false);
      }
    };

    void fetchPreAuths();
  }, [filterStatus]);

  const summary = useMemo(
    () => ({
      approved: preAuths.filter((item) => item.status === 'APPROVED').length,
      pending: preAuths.filter((item) => item.status === 'REQUESTED').length,
      total: preAuths.length,
    }),
    [preAuths]
  );

  const handleCreatePreAuth = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await apiClient.post('/pre-auths/', {
        treatment_code: formData.treatment_code,
        estimated_amount: formData.estimated_amount,
        insurance_provider: formData.insurance_provider,
      });

      setShowCreateModal(false);
      setFormData({ treatment_code: '', estimated_amount: '', insurance_provider: '' });
      setFilterStatus('');
      setLoading(true);
      const response = await apiClient.get<{ results?: PreAuth[] }>('/pre-auths/');
      setPreAuths(response.results || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to create pre-authorization');
    } finally {
      setLoading(false);
    }
  };

  const handleApprovePreAuth = async (preAuthId: number) => {
    const approvedAmount = window.prompt('Enter approved amount');
    if (!approvedAmount) return;

    try {
      await apiClient.post(`/pre-auths/${preAuthId}/approve/`, {
        approved_amount: approvedAmount,
      });

      setPreAuths((current) =>
        current.map((item) =>
          item.id === preAuthId
            ? { ...item, status: 'APPROVED', approved_amount: Number(approvedAmount) }
            : item
        )
      );
    } catch (err: any) {
      setError(err?.message || 'Failed to approve pre-authorization');
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.finance}
      title="pre-authorizations"
      description="Pre-authorization workflows are restricted to finance and insurance roles."
    >
      <PageHeader
        title="Insurance Pre-Authorization"
        description="Track treatment approvals, insurer limits, and validity windows from the finance shell."
        actions={
          <button
            type="button"
            onClick={() => setShowCreateModal(true)}
            className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700"
          >
            Request Pre-Auth
          </button>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Approved" value={summary.approved} tone="green" />
        <StatCard label="Pending" value={summary.pending} tone="blue" />
        <StatCard label="Total Requests" value={summary.total} tone="violet" />
      </div>

      <SectionCard title="Pre-Authorization Queue" subtitle="Review status, approved amounts, and remaining validity windows.">
        <div className="mb-4">
          <select
            value={filterStatus}
            onChange={(event) => setFilterStatus(event.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="REQUESTED">Requested</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="PARTIAL">Partial</option>
            <option value="EXPIRED">Expired</option>
          </select>
        </div>

        {loading ? <EmptyState title="Loading pre-authorizations" description="Refreshing payer approvals and expiry windows." /> : null}
        {!loading && error ? <EmptyState title="Pre-authorizations unavailable" description={error} /> : null}
        {!loading && !error && preAuths.length === 0 ? <EmptyState title="No pre-authorizations found" description="Create a request to start the pre-auth workflow." /> : null}

        {!loading && !error && preAuths.length > 0 ? (
          <div className="space-y-3">
            {preAuths.map((preAuth) => (
              <div key={preAuth.id} className="rounded-lg border border-gray-200 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold text-gray-900">{preAuth.pre_auth_number || `PRE-${preAuth.id}`}</p>
                      <StatusBadge value={preAuth.status} />
                    </div>
                    <p className="text-sm text-gray-700">{preAuth.patient_name}</p>
                    <p className="text-sm text-gray-600">
                      {preAuth.insurance_provider} | {preAuth.treatment_code}
                    </p>
                    <p className="text-xs text-gray-500">
                      Estimated: Rs. {preAuth.estimated_amount.toLocaleString()}
                      {preAuth.approved_amount ? ` | Approved: Rs. ${preAuth.approved_amount.toLocaleString()}` : ''}
                    </p>
                    <p className="text-xs text-gray-500">
                      Valid until: {preAuth.valid_until ? new Date(preAuth.valid_until).toLocaleDateString() : 'Pending insurer decision'}
                    </p>
                  </div>
                  {preAuth.status === 'REQUESTED' ? (
                    <button
                      type="button"
                      onClick={() => handleApprovePreAuth(preAuth.id)}
                      className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700"
                    >
                      Approve
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </SectionCard>

      {showCreateModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4">
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
            <h2 className="text-xl font-bold text-gray-900">Request Pre-Authorization</h2>
            <form onSubmit={handleCreatePreAuth} className="mt-4 space-y-4">
              <input
                type="text"
                required
                value={formData.treatment_code}
                onChange={(event) => setFormData((current) => ({ ...current, treatment_code: event.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-4 py-2"
                placeholder="Treatment code"
              />
              <input
                type="text"
                required
                value={formData.insurance_provider}
                onChange={(event) => setFormData((current) => ({ ...current, insurance_provider: event.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-4 py-2"
                placeholder="Insurance provider"
              />
              <input
                type="number"
                required
                step="0.01"
                value={formData.estimated_amount}
                onChange={(event) => setFormData((current) => ({ ...current, estimated_amount: event.target.value }))}
                className="w-full rounded-lg border border-gray-300 px-4 py-2"
                placeholder="Estimated amount"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700"
                >
                  Cancel
                </button>
                <button type="submit" className="rounded-lg bg-violet-600 px-4 py-2 text-sm font-semibold text-white hover:bg-violet-700">
                  Submit
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </ProtectedPage>
  );
}
