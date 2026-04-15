'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface Doctor {
  id: number;
  user: {
    first_name?: string;
    last_name?: string;
    username?: string;
    email?: string;
  };
}

interface Shift {
  id: number;
  name: string;
}

interface Schedule {
  id: number;
  doctor: number;
  doctor_name: string;
  day: 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN';
  shift: number;
  shift_name: string;
  is_active: boolean;
}

const DAY_LABELS: Record<Schedule['day'], string> = {
  MON: 'Monday',
  TUE: 'Tuesday',
  WED: 'Wednesday',
  THU: 'Thursday',
  FRI: 'Friday',
  SAT: 'Saturday',
  SUN: 'Sunday',
};


export default function ManageSchedulesPage() {
  const [userRole, setUserRole] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedDay, setSelectedDay] = useState<'ALL' | Schedule['day']>('ALL');
  const [selectedDoctor, setSelectedDoctor] = useState<number | 'ALL'>('ALL');
  const [formData, setFormData] = useState<{ doctor: number | ''; shift: number | ''; day: Schedule['day']; is_active: boolean }>({
    doctor: '',
    shift: '',
    day: 'MON',
    is_active: true,
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const [scheduleRes, doctorRes, shiftRes] = await Promise.all([
        apiClient.get<PaginatedResponse<Schedule>>('/schedules/'),
        apiClient.get<PaginatedResponse<Doctor>>('/doctors/'),
        apiClient.get<PaginatedResponse<Shift>>('/shifts/'),
      ]);
      setSchedules(scheduleRes.results || []);
      setDoctors(doctorRes.results || []);
      setShifts(shiftRes.results || []);
    } catch {
      toast.error('Failed to load schedules');
    } finally {
      setIsLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingId(null);
    setFormData({ doctor: '', shift: '', day: 'MON', is_active: true });
    setShowModal(true);
  };

  const openEditModal = (schedule: Schedule) => {
    setEditingId(schedule.id);
    setFormData({
      doctor: schedule.doctor,
      shift: schedule.shift,
      day: schedule.day,
      is_active: schedule.is_active,
    });
    setShowModal(true);
  };

  const saveSchedule = async () => {
    if (!formData.doctor || !formData.shift) {
      toast.error('Please select doctor and shift');
      return;
    }

    try {
      const payload = {
        doctor: formData.doctor,
        shift: formData.shift,
        day: formData.day,
        is_active: formData.is_active,
      };

      if (editingId) {
        await apiClient.patch(`/schedules/${editingId}/`, payload);
        toast.success('Schedule updated');
      } else {
        await apiClient.post('/schedules/', payload);
        toast.success('Schedule created');
      }

      setShowModal(false);
      setFormData({ doctor: '', shift: '', day: 'MON', is_active: true });
      setEditingId(null);
      fetchData();
    } catch {
      toast.error(editingId ? 'Failed to update schedule' : 'Failed to create schedule');
    }
  };

  const toggleScheduleStatus = async (schedule: Schedule) => {
    try {
      await apiClient.patch(`/schedules/${schedule.id}/`, { is_active: !schedule.is_active });
      setSchedules((prev) => prev.map((item) => (item.id === schedule.id ? { ...item, is_active: !item.is_active } : item)));
      toast.success('Schedule status updated');
    } catch {
      toast.error('Failed to update schedule status');
    }
  };

  const deleteSchedule = async (id: number) => {
    if (!confirm('Delete this schedule?')) return;
    try {
      await apiClient.delete(`/schedules/${id}/`);
      setSchedules((prev) => prev.filter((item) => item.id !== id));
      toast.success('Schedule deleted');
    } catch {
      toast.error('Failed to delete schedule');
    }
  };

  const isAdmin = userRole === 'ADMIN';

  const filteredSchedules = schedules.filter((item) => {
    if (selectedDay !== 'ALL' && item.day !== selectedDay) return false;
    if (selectedDoctor !== 'ALL' && item.doctor !== selectedDoctor) return false;
    return true;
  });

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
            <h1 className="text-3xl font-bold text-gray-900">Manage Schedules</h1>
            <p className="mt-2 text-gray-600">Assign doctors to days and shifts</p>
          </div>
          <button
            onClick={openCreateModal}
            className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            + Add Schedule
          </button>
        </div>

        <div className="grid grid-cols-1 gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm md:grid-cols-3">
          <select
            value={selectedDoctor}
            onChange={(e) => setSelectedDoctor(e.target.value === 'ALL' ? 'ALL' : Number(e.target.value))}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
          >
            <option value="ALL">All Doctors</option>
            {doctors.map((doctor) => {
              const name = `${doctor.user.first_name || ''} ${doctor.user.last_name || ''}`.trim() || doctor.user.username || doctor.user.email || `Doctor ${doctor.id}`;
              return (
                <option key={doctor.id} value={doctor.id}>{name}</option>
              );
            })}
          </select>
          <select
            value={selectedDay}
            onChange={(e) => setSelectedDay(e.target.value as 'ALL' | Schedule['day'])}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
          >
            <option value="ALL">All Days</option>
            {Object.entries(DAY_LABELS).map(([code, label]) => (
              <option key={code} value={code}>{label}</option>
            ))}
          </select>
          <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-600">
            Showing {filteredSchedules.length} schedule(s)
          </div>
        </div>

        {isLoading ? (
          <div className="rounded-lg bg-white p-8 text-center text-gray-600 shadow-sm">Loading schedules...</div>
        ) : filteredSchedules.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">No schedules found.</div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Doctor</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Day</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Shift</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredSchedules.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{item.doctor_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{DAY_LABELS[item.day]}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{item.shift_name}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      <span className={`rounded-full px-2 py-1 text-xs font-medium ${item.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {item.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="space-x-2 px-4 py-3 text-sm">
                      <button
                        onClick={() => openEditModal(item)}
                        className="rounded border border-blue-300 bg-blue-50 px-3 py-1 text-blue-700 hover:bg-blue-100"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => toggleScheduleStatus(item)}
                        className="rounded border border-amber-300 bg-amber-50 px-3 py-1 text-amber-700 hover:bg-amber-100"
                      >
                        {item.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button
                        onClick={() => deleteSchedule(item.id)}
                        className="rounded border border-red-300 bg-red-50 px-3 py-1 text-red-700 hover:bg-red-100"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
              <h2 className="mb-4 text-2xl font-bold text-gray-900">{editingId ? 'Edit Schedule' : 'Add Schedule'}</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Doctor</label>
                  <select
                    value={formData.doctor}
                    onChange={(e) => setFormData({ ...formData, doctor: Number(e.target.value) || '' })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900"
                  >
                    <option value="">Select Doctor</option>
                    {doctors.map((doctor) => {
                      const name = `${doctor.user.first_name || ''} ${doctor.user.last_name || ''}`.trim() || doctor.user.username || doctor.user.email || `Doctor ${doctor.id}`;
                      return (
                        <option key={doctor.id} value={doctor.id}>{name}</option>
                      );
                    })}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Day</label>
                  <select
                    value={formData.day}
                    onChange={(e) => setFormData({ ...formData, day: e.target.value as Schedule['day'] })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900"
                  >
                    <option value="MON">Monday</option>
                    <option value="TUE">Tuesday</option>
                    <option value="WED">Wednesday</option>
                    <option value="THU">Thursday</option>
                    <option value="FRI">Friday</option>
                    <option value="SAT">Saturday</option>
                    <option value="SUN">Sunday</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Shift</label>
                  <select
                    value={formData.shift}
                    onChange={(e) => setFormData({ ...formData, shift: Number(e.target.value) || '' })}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900"
                  >
                    <option value="">Select Shift</option>
                    {shifts.map((shift) => (
                      <option key={shift.id} value={shift.id}>{shift.name}</option>
                    ))}
                  </select>
                </div>

                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    className="h-4 w-4"
                  />
                  Mark as active
                </label>
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  onClick={() => setShowModal(false)}
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={saveSchedule}
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
