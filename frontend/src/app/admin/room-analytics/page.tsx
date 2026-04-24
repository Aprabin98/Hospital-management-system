'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface RoomSummary {
  id: number;
  room_number: string;
  room_type: string;
  floor: string;
  capacity: number;
  occupied_beds_count: number;
  available_beds_count: number;
  maintenance_beds_count: number;
  utilization_percent: number;
}

interface StatsResponse {
  kpis: {
    total_rooms: number;
    active_rooms: number;
    total_beds: number;
    occupied_beds: number;
    available_beds: number;
    maintenance_beds: number;
    occupancy_rate: number;
  };
  room_type_distribution: Array<{
    type: string;
    label: string;
    count: number;
    percent: number;
  }>;
  room_statistics?: RoomSummary[];
}

export default function RoomAnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<StatsResponse | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<StatsResponse>('/rooms/statistics/');
      setStats({
        ...response,
        room_statistics: response.room_statistics || [],
      });
    } catch {
      toast.error('Failed to load room statistics');
    } finally {
      setLoading(false);
    }
  };

  const crowdedRooms = useMemo(() => {
    if (!stats?.room_statistics) return [];
    return stats.room_statistics.filter((room) => room.utilization_percent >= 85);
  }, [stats]);

  const exportCsv = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
      const response = await fetch(`${baseURL}/rooms/statistics/export/csv/`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
      });
      if (!response.ok) {
        throw new Error('Export request failed');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'room_statistics.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Room statistics export downloaded');
    } catch {
      toast.error('Failed to export room statistics');
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Room Statistics and Export</h1>
            <p className="mt-2 text-gray-600">Track occupancy, identify room pressure, and export current utilization.</p>
          </div>
          <div className="flex gap-2">
            <button onClick={fetchStats} className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Refresh</button>
            <button onClick={exportCsv} className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700">Export CSV</button>
          </div>
        </div>

        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading room analytics...</div>
        ) : !stats ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">No room statistics found.</div>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="rounded-lg bg-white p-4 shadow-sm ring-1 ring-gray-200">
                <p className="text-sm text-gray-500">Total Rooms</p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{stats.kpis.total_rooms}</p>
              </div>
              <div className="rounded-lg bg-white p-4 shadow-sm ring-1 ring-gray-200">
                <p className="text-sm text-gray-500">Total Capacity</p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{stats.kpis.total_beds}</p>
              </div>
              <div className="rounded-lg bg-white p-4 shadow-sm ring-1 ring-gray-200">
                <p className="text-sm text-gray-500">Occupied Beds</p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{stats.kpis.occupied_beds}</p>
              </div>
              <div className="rounded-lg bg-white p-4 shadow-sm ring-1 ring-gray-200">
                <p className="text-sm text-gray-500">Overall Occupancy</p>
                <p className="mt-1 text-2xl font-bold text-gray-900">{stats.kpis.occupancy_rate}%</p>
              </div>
            </div>

            <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
              High pressure rooms (&gt;= 85% occupancy): {crowdedRooms.length}
            </div>

            <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Room</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Type</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Capacity</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Occupied</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Available</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Occupancy</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {(stats.room_statistics || []).map((room) => (
                    <tr key={room.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{room.room_number}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{room.room_type}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{room.capacity}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{room.occupied_beds_count}</td>
                      <td className="px-4 py-3 text-sm text-gray-700">{room.available_beds_count}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${room.utilization_percent >= 85 ? 'bg-red-100 text-red-700' : room.utilization_percent >= 60 ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                          {room.utilization_percent}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="text-xs text-gray-500">Room type groups: {stats.room_type_distribution.length}</p>
          </>
        )}
      </div>
    </MainLayout>
  );
}
