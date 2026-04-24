'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { ProtectedPage } from '@/components/Auth';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { ACCESS_MATRIX } from '@/lib/access';
import { PaginatedResponse } from '@/types';

interface LabTest {
  id: number;
  patient: { id: number; user: { first_name: string; last_name: string } };
  test_name: string;
  test_type: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  booking_date: string;
  completion_date?: string;
  notes?: string;
  result_file?: string;
}

export default function TestsPage() {
  const [tests, setTests] = useState<LabTest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterPriority, setFilterPriority] = useState<string>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 15;

  useEffect(() => {
    fetchTests();
  }, []);

  const fetchTests = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<LabTest>>('/lab/tests/');
      setTests(response.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tests');
      toast.error('Failed to load tests');
    } finally {
      setIsLoading(false);
    }
  };

  const statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'];
  const priorities = ['LOW', 'MEDIUM', 'HIGH', 'URGENT'];

  const statusColors: { [key: string]: string } = {
    PENDING: 'bg-yellow-100 text-yellow-800',
    IN_PROGRESS: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    CANCELLED: 'bg-red-100 text-red-800',
  };

  const priorityColors: { [key: string]: string } = {
    LOW: 'bg-gray-100 text-gray-800',
    MEDIUM: 'bg-yellow-100 text-yellow-800',
    HIGH: 'bg-orange-100 text-orange-800',
    URGENT: 'bg-red-100 text-red-800',
  };

  const filteredTests = useMemo(() => {
    let result = tests;

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (t) =>
          t.test_name.toLowerCase().includes(term) ||
          t.patient.user.first_name.toLowerCase().includes(term) ||
          t.patient.user.last_name.toLowerCase().includes(term)
      );
    }

    if (filterStatus !== 'ALL') {
      result = result.filter((t) => t.status === filterStatus);
    }

    if (filterPriority !== 'ALL') {
      result = result.filter((t) => t.priority === filterPriority);
    }

    return result;
  }, [tests, searchTerm, filterStatus, filterPriority]);

  const paginatedTests = useMemo(() => {
    const startIdx = (currentPage - 1) * pageSize;
    return filteredTests.slice(startIdx, startIdx + pageSize);
  }, [filteredTests, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredTests.length / pageSize);

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.internalTools}
      title="internal test registry"
      description="This route is restricted to administrators because it is internal tooling."
    >
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Internal Test Registry</h1>
          <p className="mt-2 text-gray-600">Administrative tooling for lab test verification and QA only.</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 rounded-lg bg-white p-4 shadow-sm">
          <input
            type="text"
            placeholder="Search by test name or patient..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />

          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Status</option>
            {statuses.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>

          <select
            value={filterPriority}
            onChange={(e) => {
              setFilterPriority(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Priorities</option>
            {priorities.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>

          <Link
            href="/lab-reports/booking"
            className="ml-auto inline-flex rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            + Book New Test
          </Link>
        </div>

        {/* Tests Table */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading tests...</div>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
        ) : filteredTests.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">
            No tests found.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="w-full">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Patient</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Test Name</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Type</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Priority</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Booked</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedTests.map((test) => (
                  <tr key={test.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <p className="font-medium text-gray-900">
                        {test.patient.user.first_name} {test.patient.user.last_name}
                      </p>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">{test.test_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-700">{test.test_type}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${priorityColors[test.priority]}`}>
                        {test.priority}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${statusColors[test.status]}`}>
                        {test.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {new Date(test.booking_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/lab-reports/booking/${test.id}`}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between rounded-lg bg-white p-4 shadow-sm">
            <div className="text-sm text-gray-600">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filteredTests.length)} of{' '}
              {filteredTests.length} tests
            </div>
            <div className="flex gap-2">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`rounded px-2 py-1 text-sm ${
                      currentPage === page
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}
