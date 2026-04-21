/**
 * Insurance Claims Management - Phase 7
 * Path: frontend/src/pages/finance/claims.tsx
 * Features: Track, submit, and manage insurance claims
 */

import { useEffect, useState } from 'react';
import axios from 'axios';
import Link from 'next/link';

interface Claim {
  id: number;
  claim_number: string;
  patient_name: string;
  insurance_provider: string;
  claimed_amount: number;
  approved_amount: number | null;
  status: string;
  days_pending: number;
  submitted_at: string;
  created_at: string;
}

export default function ClaimsPage() {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('');

  useEffect(() => {
    fetchClaims();
  }, [filterStatus]);

  const fetchClaims = async () => {
    try {
      const token = localStorage.getItem('token');
      let url = `${process.env.NEXT_PUBLIC_API_URL}/claims/`;
      if (filterStatus) url += `?status=${filterStatus}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setClaims(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  };

  const statusColors: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-700',
    SUBMITTED: 'bg-blue-100 text-blue-700',
    PROCESSING: 'bg-yellow-100 text-yellow-700',
    APPROVED: 'bg-green-100 text-green-700',
    REJECTED: 'bg-red-100 text-red-700',
    DENIED: 'bg-red-200 text-red-800',
    APPROVED_WITH_REDUCTION: 'bg-orange-100 text-orange-700',
    PENDING_MORE_INFO: 'bg-purple-100 text-purple-700',
    REWORK_NEEDED: 'bg-red-100 text-red-700',
  };

  const statusPriority: Record<string, number> = {
    PENDING_MORE_INFO: 1,
    REWORK_NEEDED: 1,
    DENIED: 2,
    REJECTED: 2,
    PROCESSING: 3,
    SUBMITTED: 4,
    APPROVED_WITH_REDUCTION: 5,
    APPROVED: 6,
    DRAFT: 7,
  };

  const sortedClaims = [...claims].sort(
    (a, b) => (statusPriority[a.status] || 10) - (statusPriority[b.status] || 10)
  );

  if (loading) return <div className="p-8 text-center">Loading claims...</div>;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Insurance Claims</h1>
            <p className="text-gray-600">Track and manage insurance claim submissions</p>
          </div>
          <Link
            href="/finance/claims/create"
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700"
          >
            + New Claim
          </Link>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {/* Status Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700 font-semibold">🔴 Needs Action</p>
            <p className="text-2xl font-bold text-red-600 mt-1">
              {claims.filter((c) => ['REJECTED', 'DENIED', 'REWORK_NEEDED'].includes(c.status)).length}
            </p>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-yellow-700 font-semibold">⏳ In Progress</p>
            <p className="text-2xl font-bold text-yellow-600 mt-1">
              {claims.filter((c) => ['SUBMITTED', 'PROCESSING'].includes(c.status)).length}
            </p>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-700 font-semibold">✅ Approved</p>
            <p className="text-2xl font-bold text-green-600 mt-1">
              {claims.filter((c) => ['APPROVED', 'APPROVED_WITH_REDUCTION'].includes(c.status)).length}
            </p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-700 font-semibold">📊 Total Claims</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">{claims.length}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <label className="text-sm font-semibold text-gray-700">Filter by Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="SUBMITTED">Submitted</option>
            <option value="PROCESSING">Processing</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="DENIED">Denied</option>
            <option value="REWORK_NEEDED">Rework Needed</option>
          </select>
        </div>

        {/* Claims Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {sortedClaims.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No claims found</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Claim #
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Patient
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Insurer
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">
                    Claimed
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-semibold text-gray-700">
                    Approved
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700">
                    Status
                  </th>
                  <th className="px-6 py-3 text-center text-xs font-semibold text-gray-700">
                    Aging
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {sortedClaims.map((claim) => (
                  <tr key={claim.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <span className="font-semibold text-gray-900">{claim.claim_number}</span>
                    </td>
                    <td className="px-6 py-4 text-sm">{claim.patient_name}</td>
                    <td className="px-6 py-4 text-sm">{claim.insurance_provider}</td>
                    <td className="px-6 py-4 text-right font-semibold">
                      Rs.{claim.claimed_amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      {claim.approved_amount ? (
                        <span className="text-green-600 font-semibold">
                          Rs.{claim.approved_amount.toLocaleString()}
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          statusColors[claim.status] || statusColors.DRAFT
                        }`}
                      >
                        {claim.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      {claim.days_pending > 0 && (
                        <span
                          className={`px-2 py-1 rounded text-sm font-semibold ${
                            claim.days_pending > 45
                              ? 'bg-red-100 text-red-700'
                              : claim.days_pending > 30
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {claim.days_pending}d
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/finance/claims/${claim.id}`}
                        className="text-blue-600 hover:text-blue-700 text-sm font-semibold"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
