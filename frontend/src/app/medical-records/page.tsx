'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { MedicalRecord, PaginatedResponse } from '@/types';
import { apiClient } from '@/lib/api';

export default function MedicalRecordsPage() {
  const [records, setRecords] = useState<MedicalRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchRecords();
  }, []);

  const fetchRecords = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<MedicalRecord>>('/medical-records/');
      setRecords(response.results || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load medical records');
      toast.error('Failed to load medical records');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Medical Records</h1>
            <p className="mt-2 text-gray-600">View and manage patient medical records</p>
          </div>
          {userRole !== 'PATIENT' && (
            <Link
              href="/medical-records/create"
              className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white transition-colors hover:bg-blue-700"
            >
              + Add Record
            </Link>
          )}
        </div>

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg text-gray-600">Loading medical records...</div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {!isLoading && records.length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
            <p className="text-gray-600">No medical records found</p>
          </div>
        )}

        {!isLoading && records.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Patient</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Allergies</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Chronic Conditions</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Last Updated</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {records.map((record: any) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {record.patient?.full_name || `Patient ${record.patient}`}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {record.allergies ? record.allergies.substring(0, 30) + '...' : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {record.chronic_conditions ? record.chronic_conditions.substring(0, 30) + '...' : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(record.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <Link
                        href={`/medical-records/${record.id}`}
                        className="text-blue-600 hover:text-blue-700"
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
      </div>
    </MainLayout>
  );
}
