'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface Shift {
  id: number;
  name: string;
  start_time: string;
  end_time: string;
  slot_duration: number;
}

export default function ManageShiftsPage() {
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', start_time: '', end_time: '', slot_duration: 30 });

  useEffect(() => {
    fetchShifts();
  }, []);

  const fetchShifts = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<Shift>>('/shifts/');
      setShifts(response.results || []);
    } catch {
      toast.error('Failed to load shifts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!formData.name || !formData.start_time || !formData.end_time) {
      toast.error('Please fill all required fields');
      return;
    }

    try {
      await apiClient.post('/shifts/', formData);
      toast.success('Shift created successfully');
      setShowModal(false);
      setFormData({ name: '', start_time: '', end_time: '', slot_duration: 30 });
      fetchShifts();
    } catch {
      toast.error('Failed to create shift');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure?')) return;
    try {
      await apiClient.delete(`/shifts/${id}/`);
      setShifts((prev) => prev.filter((s) => s.id !== id));
      toast.success('Shift deleted');
    } catch {
      toast.error('Failed to delete shift');
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Manage Shifts</h1>
            <p className="mt-2 text-gray-600">Configure doctor work shifts and time slots</p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            + Add Shift
          </button>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading...</div>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {shifts.map((shift) => (
              <div key={shift.id} className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                <h3 className="mb-2 font-semibold text-gray-900">{shift.name}</h3>
                <div className="mb-4 space-y-1 text-sm text-gray-700">
                  <p>⏰ {shift.start_time} - {shift.end_time}</p>
                  <p>⏱️ Slot: {shift.slot_duration} min</p>
                </div>
                <button
                  onClick={() => handleDelete(shift.id)}
                  className="w-full rounded border border-red-300 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-100"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
              <h2 className="mb-4 text-2xl font-bold text-gray-900">Add Shift</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Shift Name *</label>
                  <select
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select shift</option>
                    <option value="Morning">Morning</option>
                    <option value="Evening">Evening</option>
                    <option value="Night">Night</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Start Time *</label>
                  <input
                    type="time"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">End Time *</label>
                  <input
                    type="time"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Slot Duration (minutes)</label>
                  <input
                    type="number"
                    min="15"
                    step="15"
                    value={formData.slot_duration}
                    onChange={(e) => setFormData({ ...formData, slot_duration: parseInt(e.target.value) })}
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
                  onClick={handleSave}
                  className="flex-1 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
