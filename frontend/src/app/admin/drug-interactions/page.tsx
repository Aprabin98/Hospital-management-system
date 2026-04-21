'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface DrugInteraction {
  id: number;
  drug1: string;
  drug2: string;
  severity: 'MINOR' | 'MODERATE' | 'MAJOR' | 'CONTRAINDICATED';
  description: string;
  action: string;
  is_active: boolean;
}

export default function DrugInteractionsPage() {
  const [interactions, setInteractions] = useState<DrugInteraction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRoleLoading, setIsRoleLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<{ drug1: string; drug2: string; severity: 'MINOR' | 'MODERATE' | 'MAJOR' | 'CONTRAINDICATED'; description: string; action: string }>({
    drug1: '',
    drug2: '',
    severity: 'MODERATE',
    description: '',
    action: '',
  });

  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    const role = (localStorage.getItem('userRole') || '').toUpperCase();
    setUserRole(role);
    setIsRoleLoading(false);

    if (role === 'ADMIN') {
      fetchInteractions();
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchInteractions = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<DrugInteraction>>('/drug-interactions/');
      setInteractions(response.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load interactions');
      toast.error('Failed to load interactions');
    } finally {
      setIsLoading(false);
    }
  };

  const severityColors: { [key: string]: string } = {
    MINOR: 'bg-green-100 text-green-800',
    MODERATE: 'bg-yellow-100 text-yellow-800',
    MAJOR: 'bg-orange-100 text-orange-800',
    CONTRAINDICATED: 'bg-red-100 text-red-800',
  };

  const filteredInteractions = useMemo(() => {
    let result = interactions;

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (i) =>
          i.drug1.toLowerCase().includes(term) ||
          i.drug2.toLowerCase().includes(term) ||
          i.description.toLowerCase().includes(term)
      );
    }

    if (filterSeverity !== 'ALL') {
      result = result.filter((i) => i.severity === filterSeverity);
    }

    return result;
  }, [interactions, searchTerm, filterSeverity]);

  const handleCreate = async () => {
    if (!formData.drug1 || !formData.drug2) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      await apiClient.post('/drug-interactions/', formData);
      toast.success('Interaction recorded successfully');
      setShowModal(false);
      setFormData({ drug1: '', drug2: '', severity: 'MODERATE', description: '', action: '' });
      fetchInteractions();
    } catch {
      toast.error('Failed to create interaction');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return;
    try {
      await apiClient.delete(`/drug-interactions/${id}/`);
      setInteractions((prev) => prev.filter((i) => i.id !== id));
      toast.success('Interaction deleted');
    } catch {
      toast.error('Failed to delete interaction');
    }
  };

  if (isRoleLoading) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-gray-500">Loading...</div>
        </div>
      </MainLayout>
    );
  }

  if (!isAdmin) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Drug Interactions</h1>
            <p className="mt-2 text-gray-600">Manage drug-drug interaction records and safety alerts</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            + Report Interaction
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-4 rounded-lg bg-white p-4 shadow-sm">
          <input
            type="text"
            placeholder="Search by drug name or description..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
            }}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Severities</option>
            <option value="MINOR">Minor</option>
            <option value="MODERATE">Moderate</option>
            <option value="MAJOR">Major</option>
            <option value="CONTRAINDICATED">Contraindicated</option>
          </select>
        </div>

        {/* Interactions List */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading...</div>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
        ) : filteredInteractions.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">
            No interactions found.
          </div>
        ) : (
          <div className="space-y-4">
            {filteredInteractions.map((interaction) => (
              <div key={interaction.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm hover:shadow-md">
                <div className="mb-3 flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {interaction.drug1} ↔ {interaction.drug2}
                    </h3>
                    <p className="text-sm text-gray-600">{interaction.description}</p>
                  </div>
                  <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${severityColors[interaction.severity]}`}>
                    {interaction.severity}
                  </span>
                </div>

                <div className="mb-3 rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                  <p className="font-medium">Recommended Action:</p>
                  <p className="mt-1">{interaction.action}</p>
                </div>

                <button
                  onClick={() => handleDelete(interaction.id)}
                  className="rounded border border-red-300 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-100"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
              <h2 className="mb-4 text-2xl font-bold text-gray-900">Report Drug Interaction</h2>

              <div className="space-y-4">
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Drug 1 *</label>
                    <input
                      type="text"
                      value={formData.drug1}
                      onChange={(e) => setFormData({ ...formData, drug1: e.target.value })}
                      className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Drug 2 *</label>
                    <input
                      type="text"
                      value={formData.drug2}
                      onChange={(e) => setFormData({ ...formData, drug2: e.target.value })}
                      className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Severity</label>
                  <select
                    value={formData.severity}
                    onChange={(e) => setFormData({ ...formData, severity: e.target.value as 'MINOR' | 'MODERATE' | 'MAJOR' | 'CONTRAINDICATED' })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="MINOR">Minor</option>
                    <option value="MODERATE">Moderate</option>
                    <option value="MAJOR">Major</option>
                    <option value="CONTRAINDICATED">Contraindicated</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Recommended Action</label>
                  <textarea
                    value={formData.action}
                    onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                    rows={2}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => setShowModal(false)}
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
                >
                  Report
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
