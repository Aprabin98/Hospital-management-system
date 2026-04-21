/**
 * Denial Rework Queue - Phase 7
 * Path: frontend/src/pages/finance/denials.tsx
 * Features: Manage denied claims and rework process
 */

import { useEffect, useState } from 'react';
import axios from 'axios';

interface DenialRework {
  id: number;
  claim_number: string;
  patient_name: string;
  original_denial_reason: string;
  status: string;
  assigned_to_name: string | null;
  correction_notes: string;
  resubmit_date: string | null;
  created_at: string;
  updated_at: string;
}

export default function DenialReworksPage() {
  const [reworks, setReworks] = useState<DenialRework[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filterStatus, setFilterStatus] = useState('PENDING_REVIEW');
  const [selectedRework, setSelectedRework] = useState<DenialRework | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchReworks();
  }, [filterStatus]);

  const fetchReworks = async () => {
    try {
      const token = localStorage.getItem('token');
      let url = `${process.env.NEXT_PUBLIC_API_URL}/denial-reworks/`;
      if (filterStatus === 'PENDING') {
        url += 'pending/';
      } else if (filterStatus) {
        url += `?status=${filterStatus}`;
      }

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
      });

      setReworks(response.data.results || response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load denial reworks');
    } finally {
      setLoading(false);
    }
  };

  const statusColors: Record<string, string> = {
    PENDING_REVIEW: 'bg-red-100 text-red-700',
    UNDER_CORRECTION: 'bg-yellow-100 text-yellow-700',
    RESUBMITTED: 'bg-blue-100 text-blue-700',
    RESOLVED: 'bg-green-100 text-green-700',
    ABANDONED: 'bg-gray-100 text-gray-700',
  };

  const handleAssign = async (reworkId: number) => {
    const userRole = localStorage.getItem('userRole');
    if (userRole !== 'INSURANCE_COORDINATOR' && userRole !== 'ADMIN') {
      alert('Only Insurance Coordinators can assign reworks');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const billingOfficerId = prompt('Enter Billing Officer ID:');
      if (!billingOfficerId) return;

      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/denial-reworks/${reworkId}/assign/`,
        { assigned_to_id: billingOfficerId },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert('Rework assigned successfully');
      fetchReworks();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to assign rework');
    }
  };

  const handleResubmit = async (reworkId: number) => {
    const userRole = localStorage.getItem('userRole');
    if (userRole !== 'BILLING_OFFICER' && userRole !== 'ADMIN') {
      alert('Only Billing Officers can resubmit reworks');
      return;
    }

    const correctionNotes = prompt('Enter correction notes:');
    if (!correctionNotes) return;

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_URL}/denial-reworks/${reworkId}/resubmit/`,
        { correction_notes: correctionNotes, submission_notes: correctionNotes },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      alert('Claim resubmitted successfully');
      fetchReworks();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to resubmit claim');
    }
  };

  if (loading) return <div className="p-8 text-center">Loading denial reworks...</div>;

  const pendingCount = reworks.filter((r) => r.status === 'PENDING_REVIEW').length;
  const underCorrectionCount = reworks.filter((r) => r.status === 'UNDER_CORRECTION').length;

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Denial Rework Queue</h1>
          <p className="text-gray-600">Manage rejected and denied insurance claims</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
            {error}
          </div>
        )}

        {/* Alert Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-red-50 border-2 border-red-200 rounded-lg p-6">
            <p className="text-red-700 font-semibold text-lg">🔴 Pending Review</p>
            <p className="text-3xl font-bold text-red-600 mt-2">{pendingCount}</p>
            <p className="text-sm text-red-600 mt-1">Awaiting coordinator review</p>
          </div>
          <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-6">
            <p className="text-yellow-700 font-semibold text-lg">🔧 Under Correction</p>
            <p className="text-3xl font-bold text-yellow-600 mt-2">{underCorrectionCount}</p>
            <p className="text-sm text-yellow-600 mt-1">Being corrected by billing officer</p>
          </div>
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6">
            <p className="text-blue-700 font-semibold text-lg">📋 Total Reworks</p>
            <p className="text-3xl font-bold text-blue-600 mt-2">{reworks.length}</p>
            <p className="text-sm text-blue-600 mt-1">In rework queue</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <label className="text-sm font-semibold text-gray-700">Filter by Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="mt-2 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="PENDING_REVIEW">Pending Review</option>
            <option value="UNDER_CORRECTION">Under Correction</option>
            <option value="RESUBMITTED">Resubmitted</option>
            <option value="RESOLVED">Resolved</option>
            <option value="ABANDONED">Abandoned</option>
          </select>
        </div>

        {/* Reworks Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {reworks.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No denial reworks found</div>
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
                    Denial Reason
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">
                    Assigned To
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
                {reworks.map((rework) => (
                  <tr key={rework.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <span className="font-semibold text-gray-900">{rework.claim_number}</span>
                    </td>
                    <td className="px-6 py-4 text-sm">{rework.patient_name}</td>
                    <td className="px-6 py-4 text-sm max-w-md">
                      <p className="truncate text-gray-700">{rework.original_denial_reason}</p>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {rework.assigned_to_name ? (
                        <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-sm">
                          {rework.assigned_to_name}
                        </span>
                      ) : (
                        <span className="text-gray-400">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          statusColors[rework.status] || statusColors.PENDING_REVIEW
                        }`}
                      >
                        {rework.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {rework.status === 'PENDING_REVIEW' && (
                          <button
                            onClick={() => handleAssign(rework.id)}
                            className="text-orange-600 hover:text-orange-700 text-sm font-semibold"
                          >
                            Assign
                          </button>
                        )}
                        {rework.status === 'UNDER_CORRECTION' && (
                          <button
                            onClick={() => handleResubmit(rework.id)}
                            className="text-green-600 hover:text-green-700 text-sm font-semibold"
                          >
                            Resubmit
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setSelectedRework(rework);
                            setShowModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-700 text-sm font-semibold"
                        >
                          Details
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Details Modal */}
        {showModal && selectedRework && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-96 overflow-y-auto">
              <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-xl font-bold text-gray-900">
                  {selectedRework.claim_number} - {selectedRework.patient_name}
                </h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-gray-400 hover:text-gray-600 text-2xl"
                >
                  ×
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <p className="text-sm font-semibold text-gray-700">Denial Reason:</p>
                  <p className="text-gray-900 mt-1">{selectedRework.original_denial_reason}</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-700">Status:</p>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-semibold inline-block mt-1 ${
                      statusColors[selectedRework.status]
                    }`}
                  >
                    {selectedRework.status.replace(/_/g, ' ')}
                  </span>
                </div>
                {selectedRework.correction_notes && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700">Correction Notes:</p>
                    <p className="text-gray-900 mt-1">{selectedRework.correction_notes}</p>
                  </div>
                )}
                {selectedRework.assigned_to_name && (
                  <div>
                    <p className="text-sm font-semibold text-gray-700">Assigned To:</p>
                    <p className="text-gray-900 mt-1">{selectedRework.assigned_to_name}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
