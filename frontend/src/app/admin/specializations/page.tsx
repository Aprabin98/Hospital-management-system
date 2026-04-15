'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface Specialization {
  id: number;
  name: string;
  description: string;
  icon?: string;
  is_active: boolean;
  created_at: string;
}

export default function SpecializationsPage() {
  const [specs, setSpecs] = useState<Specialization[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '', icon: '' });

  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchSpecializations();
  }, []);

  const fetchSpecializations = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<Specialization>>('/specializations/');
      setSpecs(response.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load specializations');
      toast.error('Failed to load specializations');
    } finally {
      setIsLoading(false);
    }
  };

  const filteredSpecs = useMemo(() => {
    if (!searchTerm.trim()) return specs;
    const term = searchTerm.toLowerCase();
    return specs.filter(
      (s) =>
        s.name.toLowerCase().includes(term) ||
        s.description.toLowerCase().includes(term)
    );
  }, [specs, searchTerm]);

  const handleSave = async () => {
    if (!formData.name) {
      toast.error('Specialization name is required');
      return;
    }

    try {
      if (editingId) {
        await apiClient.patch(`/specializations/${editingId}/`, formData);
        toast.success('Specialization updated');
      } else {
        await apiClient.post('/specializations/', formData);
        toast.success('Specialization created');
      }
      setShowModal(false);
      setEditingId(null);
      setFormData({ name: '', description: '', icon: '' });
      fetchSpecializations();
    } catch {
      toast.error(editingId ? 'Failed to update' : 'Failed to create');
    }
  };

  const handleToggleActive = async (id: number, currentStatus: boolean) => {
    try {
      await apiClient.patch(`/specializations/${id}/`, { is_active: !currentStatus });
      setSpecs((prev) =>
        prev.map((s) => (s.id === id ? { ...s, is_active: !currentStatus } : s))
      );
      toast.success('Specialization status updated');
    } catch {
      toast.error('Failed to update status');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return;
    try {
      await apiClient.delete(`/specializations/${id}/`);
      setSpecs((prev) => prev.filter((s) => s.id !== id));
      toast.success('Specialization deleted');
    } catch {
      toast.error('Failed to delete');
    }
  };

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
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Manage Specializations</h1>
            <p className="mt-2 text-gray-600">Create and manage doctor specializations</p>
          </div>
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({ name: '', description: '', icon: '' });
              setShowModal(true);
            }}
            className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            + Add Specialization
          </button>
        </div>

        <div className="rounded-lg bg-white p-4 shadow-sm">
          <input
            type="text"
            placeholder="Search specializations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading...</div>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredSpecs.map((spec) => (
              <div key={spec.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                <div className="mb-3 flex items-start justify-between">
                  <h3 className="font-semibold text-gray-900">{spec.name}</h3>
                  <button
                    onClick={() => handleToggleActive(spec.id, spec.is_active)}
                    className={`rounded-full px-2 py-1 text-xs font-medium ${
                      spec.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {spec.is_active ? 'Active' : 'Inactive'}
                  </button>
                </div>
                <p className="mb-4 text-sm text-gray-600">{spec.description}</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setEditingId(spec.id);
                      setFormData({ name: spec.name, description: spec.description, icon: spec.icon || '' });
                      setShowModal(true);
                    }}
                    className="flex-1 rounded border border-blue-300 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700 hover:bg-blue-100"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleDelete(spec.id)}
                    className="flex-1 rounded border border-red-300 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-100"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
              <h2 className="mb-4 text-2xl font-bold text-gray-900">
                {editingId ? 'Edit Specialization' : 'Add Specialization'}
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={3}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Icon</label>
                  <input
                    type="text"
                    value={formData.icon}
                    onChange={(e) => setFormData({ ...formData, icon: e.target.value })}
                    placeholder="e.g., heart, brain, bone"
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  onClick={handleSave}
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
                >
                  {editingId ? 'Update' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
