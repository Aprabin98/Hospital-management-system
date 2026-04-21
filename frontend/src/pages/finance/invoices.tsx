/**
 * Invoice Management - Phase 7
 * Path: frontend/src/pages/finance/invoices.tsx
 * Features: Create, manage, and track invoices (Proforma → Final)
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import axios from 'axios';
import Link from 'next/link';

interface Invoice {
  id: number;
  invoice_number: string;
  invoice_type: string;
  patient_name: string;
  total_amount: number;
  amount_paid: number;
  status: string;
  due_date: string;
  created_at: string;
}

export default function InvoicesPage() {
  const router = useRouter();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    fetchInvoices();
  }, [filterStatus]);

  const fetchInvoices = async () => {
    try {
      const token = localStorage.getItem('token');
      let url = `${process.env.NEXT_PUBLIC_API_URL}/invoices/`;
      if (filterStatus) url += `?status=${filterStatus}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setInvoices(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load invoices');
    } finally {
      setLoading(false);
    }
  };

  const handleFinalize = async (invoiceId: number) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/invoices/${invoiceId}/finalize/`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('Invoice finalized successfully');
      fetchInvoices();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to finalize invoice');
    }
  };

  const statusColors: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-700',
    ISSUED: 'bg-blue-100 text-blue-700',
    PAID: 'bg-green-100 text-green-700',
    PARTIALLY_PAID: 'bg-yellow-100 text-yellow-700',
    OVERDUE: 'bg-red-100 text-red-700',
    CANCELLED: 'bg-gray-200 text-gray-600',
  };

  if (loading) return <div className="p-8 text-center">Loading invoices...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Invoices</h1>
            <p className="text-gray-600">Proforma & Final Invoice Management</p>
          </div>
          <Link
            href="/finance/invoices/create"
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
          >
            + Create Invoice
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <label className="text-sm font-semibold text-gray-700">Filter by Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="ISSUED">Issued</option>
            <option value="PAID">Fully Paid</option>
            <option value="PARTIALLY_PAID">Partially Paid</option>
            <option value="OVERDUE">Overdue</option>
          </select>
        </div>

        {/* Invoices Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {invoices.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No invoices found</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Invoice Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Type
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">
                    Paid
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <span className="font-semibold text-gray-900">{invoice.invoice_number}</span>
                    </td>
                    <td className="px-6 py-4">{invoice.patient_name}</td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-600">{invoice.invoice_type}</span>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold">
                      Rs.{invoice.total_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right text-green-600 font-semibold">
                      Rs.{invoice.amount_paid.toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          statusColors[invoice.status] || statusColors.DRAFT
                        }`}
                      >
                        {invoice.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <Link
                          href={`/finance/invoices/${invoice.id}`}
                          className="text-blue-600 hover:text-blue-700 text-sm font-semibold"
                        >
                          View
                        </Link>
                        {invoice.invoice_type === 'PROFORMA' && invoice.status === 'DRAFT' && (
                          <button
                            onClick={() => handleFinalize(invoice.id)}
                            className="text-green-600 hover:text-green-700 text-sm font-semibold"
                          >
                            Finalize
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Total Invoices</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">{invoices.length}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Total Amount</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              Rs.{invoices.reduce((sum, inv) => sum + inv.total_amount, 0).toLocaleString()}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-gray-600 text-sm">Total Collected</p>
            <p className="text-3xl font-bold text-green-600 mt-2">
              Rs.{invoices.reduce((sum, inv) => sum + inv.amount_paid, 0).toLocaleString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
