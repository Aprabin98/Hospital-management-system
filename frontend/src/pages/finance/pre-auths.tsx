/**
 * Insurance Pre-Authorization Management - Phase 7
 * Path: frontend/src/pages/finance/pre-auths.tsx
 * Features: Request and track pre-authorizations for treatments
 */

import { useEffect, useState } from 'react';
import axios from 'axios';
import Link from 'next/link';

interface PreAuth {
  id: number;
  patient_name: string;
  insurance_provider: string;
  treatment_code: string;
  estimated_amount: number;
  approved_amount: number | null;
  status: string;
  pre_auth_number: string | null;
  valid_from: string | null;
  valid_until: string | null;
  created_at: string;
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
    fetchPreAuths();
  }, [filterStatus]);

  const fetchPreAuths = async () => {
    try {
      const token = localStorage.getItem('token');
      let url = `${process.env.NEXT_PUBLIC_API_URL}/pre-auths/`;
      if (filterStatus) url += `?status=${filterStatus}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setPreAuths(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load pre-authorizations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePreAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/pre-auths/`,
        {
          treatment_code: formData.treatment_code,
          estimated_amount: formData.estimated_amount,
          insurance_provider: formData.insurance_provider,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert('Pre-authorization request created successfully');
      setFormData({ treatment_code: '', estimated_amount: '', insurance_provider: '' });
      setShowCreateModal(false);
      fetchPreAuths();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create pre-authorization');
    }
  };

  const handleApprovePreAuth = async (preAuthId: number, approvedAmount: string) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/pre-auths/${preAuthId}/approve/`,
        { approved_amount: approvedAmount },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert('Pre-authorization approved');
      fetchPreAuths();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve pre-authorization');
    }
  };

  const statusColors: Record<string, string> = {
    REQUESTED: 'bg-blue-100 text-blue-700',
    APPROVED: 'bg-green-100 text-green-700',
    REJECTED: 'bg-red-100 text-red-700',
    PARTIAL: 'bg-yellow-100 text-yellow-700',
    EXPIRED: 'bg-gray-100 text-gray-700',
  };

  if (loading) return <div className="p-8 text-center">Loading pre-authorizations...</div>;

  const approvedCount = preAuths.filter((p) => p.status === 'APPROVED').length;
  const pendingCount = preAuths.filter((p) => p.status === 'REQUESTED').length;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Pre-Authorization</h1>
            <p className="text-gray-600">Treatment pre-authorization requests and approvals</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700"
          >
            + Request Pre-Auth
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <p className="text-green-700 font-semibold text-lg">✅ Approved</p>
            <p className="text-3xl font-bold text-green-600 mt-2">{approvedCount}</p>
            <p className="text-sm text-green-600 mt-1">Ready for treatment</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <p className="text-blue-700 font-semibold text-lg">⏳ Pending</p>
            <p className="text-3xl font-bold text-blue-600 mt-2">{pendingCount}</p>
            <p className="text-sm text-blue-600 mt-1">Awaiting insurer approval</p>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <p className="text-purple-700 font-semibold text-lg">📋 Total Requests</p>
            <p className="text-3xl font-bold text-purple-600 mt-2">{preAuths.length}</p>
            <p className="text-sm text-purple-600 mt-1">In the system</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <label className="text-sm font-semibold text-gray-700">Filter by Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="">All Statuses</option>
            <option value="REQUESTED">Requested</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="PARTIAL">Partial</option>
            <option value="EXPIRED">Expired</option>
          </select>
        </div>

        {/* Pre-Auths Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {preAuths.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No pre-authorizations found</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Pre-Auth #
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Insurer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Treatment
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">
                    Estimated
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">
                    Approved
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Valid Until
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {preAuths.map((preAuth) => (
                  <tr key={preAuth.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <span className="font-semibold text-gray-900">
                        {preAuth.pre_auth_number || '—'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">{preAuth.patient_name}</td>
                    <td className="px-6 py-4 text-sm">{preAuth.insurance_provider}</td>
                    <td className="px-6 py-4 text-sm">{preAuth.treatment_code}</td>
                    <td className="px-6 py-4 text-right font-semibold">
                      Rs.{preAuth.estimated_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {preAuth.approved_amount ? (
                        <span className="text-green-600 font-semibold">
                          Rs.{preAuth.approved_amount.toLocaleString()}
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          statusColors[preAuth.status] || statusColors.REQUESTED
                        }`}
                      >
                        {preAuth.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {preAuth.valid_until
                        ? new Date(preAuth.valid_until).toLocaleDateString()
                        : '—'}
                    </td>
                    <td className="px-6 py-4">
                      {preAuth.status === 'REQUESTED' && (
                        <button
                          onClick={() => {
                            const amount = prompt('Enter approved amount:');
                            if (amount) handleApprovePreAuth(preAuth.id, amount);
                          }}
                          className="text-green-600 hover:text-green-700 text-sm font-semibold"
                        >
                          Approve
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Create Pre-Auth Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-md w-full">
              <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-900">Request Pre-Authorization</h2>
                <button
                  onClick={() => setShowCreateModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              <form onSubmit={handleCreatePreAuth} className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Treatment Code
                  </label>
                  <input
                    type="text"
                    value={formData.treatment_code}
                    onChange={(e) =>
                      setFormData({ ...formData, treatment_code: e.target.value })
                    }
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g., CARDIAC_BYPASS"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Insurance Provider
                  </label>
                  <input
                    type="text"
                    value={formData.insurance_provider}
                    onChange={(e) =>
                      setFormData({ ...formData, insurance_provider: e.target.value })
                    }
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="e.g., Aetna, UnitedHealth"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Estimated Cost (Rs.)
                  </label>
                  <input
                    type="number"
                    value={formData.estimated_amount}
                    onChange={(e) =>
                      setFormData({ ...formData, estimated_amount: e.target.value })
                    }
                    required
                    step="0.01"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="0.00"
                  />
                </div>
                <div className="flex gap-3 justify-end pt-4">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                  >
                    Submit Request
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
