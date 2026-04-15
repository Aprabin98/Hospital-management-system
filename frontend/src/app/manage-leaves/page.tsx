'use client';

import React, { useEffect, useState } from 'react';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface DoctorLeave {
  id: number;
  date: string;
  reason: string;
  created_at: string;
}

const getTodayDateString = () => {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

export default function ManageLeavesPage() {
  const [leaves, setLeaves] = useState<DoctorLeave[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [date, setDate] = useState('');
  const [reason, setReason] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const todayMin = getTodayDateString();

  useEffect(() => {
    fetchLeaves();
  }, []);

  const fetchLeaves = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<{ results: DoctorLeave[] }>('/doctor-leaves/');
      setLeaves(response.results || []);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load leaves');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setDate('');
    setReason('');
    setEditingId(null);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!date) {
      toast.error('Please choose a leave date');
      return;
    }

    if (date < todayMin) {
      toast.error('Past leave dates are not allowed');
      return;
    }

    try {
      setIsSaving(true);
      if (editingId) {
        await apiClient.patch(`/doctor-leaves/${editingId}/`, { date, reason });
        toast.success('Leave updated');
      } else {
        await apiClient.post('/doctor-leaves/', { date, reason });
        toast.success('Leave added');
      }
      resetForm();
      fetchLeaves();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to save leave');
    } finally {
      setIsSaving(false);
    }
  };

  const onEdit = (leave: DoctorLeave) => {
    setEditingId(leave.id);
    setDate(leave.date);
    setReason(leave.reason || '');
  };

  const onDelete = async (id: number) => {
    try {
      await apiClient.delete(`/doctor-leaves/${id}/`);
      toast.success('Leave deleted');
      if (editingId === id) {
        resetForm();
      }
      fetchLeaves();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to delete leave');
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Manage Leaves</h1>
          <p className="mt-2 text-gray-600">Add, edit, and remove your leave dates</p>
        </div>

        <form onSubmit={onSubmit} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Leave Date</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                min={todayMin}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Reason (optional)</label>
              <input
                type="text"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Personal, conference, emergency, etc."
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={isSaving}
              className="rounded-lg bg-blue-600 px-5 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400"
            >
              {isSaving ? 'Saving...' : editingId ? 'Update Leave' : 'Add Leave'}
            </button>
            {editingId && (
              <button
                type="button"
                onClick={resetForm}
                className="rounded-lg border border-gray-300 px-5 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-100"
              >
                Cancel Edit
              </button>
            )}
          </div>
        </form>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Your Leaves</h2>

          {isLoading ? (
            <p className="text-gray-600">Loading leaves...</p>
          ) : leaves.length === 0 ? (
            <p className="text-gray-600">No leave entries yet.</p>
          ) : (
            <div className="space-y-3">
              {leaves.map((leave) => (
                <div key={leave.id} className="flex flex-col gap-3 rounded-lg border border-gray-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{leave.date}</p>
                    <p className="text-sm text-gray-600">{leave.reason || 'No reason provided'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => onEdit(leave)}
                      className="rounded-md border border-blue-300 px-3 py-1.5 text-sm font-medium text-blue-700 hover:bg-blue-50"
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(leave.id)}
                      className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
