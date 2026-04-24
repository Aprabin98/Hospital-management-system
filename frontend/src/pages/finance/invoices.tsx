import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/Auth';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface Invoice {
  id: number;
  invoice_number: string;
  invoice_type: string;
  patient_name: string;
  total_amount: number;
  amount_paid: number;
  status: string;
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    const fetchInvoices = async () => {
      try {
        setLoading(true);
        setError('');
        const response = await apiClient.get<{ results?: Invoice[] }>('/invoices/', {
          params: filterStatus ? { status: filterStatus } : {},
        });
        setInvoices(response.results || []);
      } catch (err: any) {
        setError(err?.message || 'Failed to load invoices');
      } finally {
        setLoading(false);
      }
    };

    void fetchInvoices();
  }, [filterStatus]);

  const totals = useMemo(
    () => ({
      count: invoices.length,
      totalAmount: invoices.reduce((sum, invoice) => sum + invoice.total_amount, 0),
      totalCollected: invoices.reduce((sum, invoice) => sum + invoice.amount_paid, 0),
    }),
    [invoices]
  );

  const handleFinalize = async (invoiceId: number) => {
    try {
      await apiClient.post(`/invoices/${invoiceId}/finalize/`, {});
      setInvoices((current) =>
        current.map((invoice) =>
          invoice.id === invoiceId
            ? { ...invoice, status: 'ISSUED' }
            : invoice
        )
      );
    } catch (err: any) {
      setError(err?.message || 'Failed to finalize invoice');
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.finance}
      title="invoice management"
      description="Invoice workflows are restricted to finance and insurance roles."
    >
      <PageHeader
        title="Invoices"
        description="Manage draft, issued, and paid invoices inside the shared finance shell."
        actions={
          <Link href="/finance/dashboard" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
            Back to Dashboard
          </Link>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Total Invoices" value={totals.count} tone="blue" />
        <StatCard label="Total Amount" value={`Rs. ${totals.totalAmount.toLocaleString()}`} />
        <StatCard label="Collected" value={`Rs. ${totals.totalCollected.toLocaleString()}`} tone="green" />
      </div>

      <SectionCard title="Invoice Ledger" subtitle="Track invoice status and finalize proforma drafts from one queue.">
        <div className="mb-4">
          <select
            value={filterStatus}
            onChange={(event) => setFilterStatus(event.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm"
          >
            <option value="">All statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="ISSUED">Issued</option>
            <option value="PAID">Fully Paid</option>
            <option value="PARTIALLY_PAID">Partially Paid</option>
            <option value="OVERDUE">Overdue</option>
          </select>
        </div>

        {loading ? <EmptyState title="Loading invoices" description="Refreshing invoice balances and statuses." /> : null}
        {!loading && error ? <EmptyState title="Invoices unavailable" description={error} /> : null}
        {!loading && !error && invoices.length === 0 ? <EmptyState title="No invoices found" description="Invoices will appear here as billing is issued." /> : null}

        {!loading && !error && invoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Invoice</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Patient</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Type</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Amount</th>
                  <th className="px-4 py-3 text-right font-semibold text-gray-700">Paid</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-semibold text-gray-900">{invoice.invoice_number}</td>
                    <td className="px-4 py-3 text-gray-700">{invoice.patient_name}</td>
                    <td className="px-4 py-3 text-gray-700">{invoice.invoice_type}</td>
                    <td className="px-4 py-3 text-right text-gray-900">Rs. {invoice.total_amount.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right text-gray-900">Rs. {invoice.amount_paid.toLocaleString()}</td>
                    <td className="px-4 py-3"><StatusBadge value={invoice.status.replaceAll('_', ' ')} /></td>
                    <td className="px-4 py-3">
                      {invoice.invoice_type === 'PROFORMA' && invoice.status === 'DRAFT' ? (
                        <button
                          type="button"
                          onClick={() => handleFinalize(invoice.id)}
                          className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700"
                        >
                          Finalize
                        </button>
                      ) : (
                        <span className="text-xs text-gray-500">No action</span>
                      )}
                    </td>
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
