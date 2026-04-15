'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface RoomBed {
  id: number;
  room: number;
  room_number: string;
  bed_number: string;
  status: 'AVAILABLE' | 'OCCUPIED' | 'MAINTENANCE';
}

interface RoomItem {
  id: number;
  room_number: string;
  room_type: 'GENERAL' | 'SEMI_PRIVATE' | 'PRIVATE' | 'ICU' | 'EMERGENCY';
  floor: string;
  capacity: number;
  is_active: boolean;
  occupied_beds: number;
  available_beds: number;
  notes: string;
  beds: RoomBed[];
}

interface RoomFormState {
  room_number: string;
  room_type: RoomItem['room_type'];
  floor: string;
  capacity: string;
  notes: string;
  is_active: boolean;
}

export default function RoomsManagementPage() {
  const [userRole, setUserRole] = useState('');
  const [loading, setLoading] = useState(true);
  const [rooms, setRooms] = useState<RoomItem[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [form, setForm] = useState<RoomFormState>({
    room_number: '',
    room_type: 'GENERAL',
    floor: '',
    capacity: '1',
    notes: '',
    is_active: true,
  });

  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get<RoomItem[]>('/rooms/available/');
      setRooms(Array.isArray(response) ? response : []);
    } catch {
      toast.error('Failed to load rooms');
    } finally {
      setLoading(false);
    }
  };

  const filteredRooms = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return rooms;
    return rooms.filter((room) => {
      return (
        room.room_number.toLowerCase().includes(term) ||
        room.room_type.toLowerCase().includes(term) ||
        room.floor.toLowerCase().includes(term)
      );
    });
  }, [rooms, searchTerm]);

  const createRoom = async () => {
    try {
      setCreating(true);
      await apiClient.post('/rooms/create/', {
        room_number: form.room_number,
        room_type: form.room_type,
        floor: form.floor,
        capacity: Number(form.capacity || 1),
        notes: form.notes,
        is_active: form.is_active,
      });
      toast.success('Room created successfully');
      setShowCreate(false);
      setForm({ room_number: '', room_type: 'GENERAL', floor: '', capacity: '1', notes: '', is_active: true });
      fetchRooms();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to create room');
    } finally {
      setCreating(false);
    }
  };

  if (!isAdmin) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">Back to Dashboard</Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Rooms Management</h1>
            <p className="mt-2 text-gray-600">Add new rooms, review capacity, and keep ward inventory current.</p>
          </div>
          <button onClick={() => setShowCreate(true)} className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700">+ Add Room</button>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by room number, type, or floor"
            className="w-full rounded-lg border border-gray-300 px-4 py-2"
          />
        </div>

        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading rooms...</div>
        ) : filteredRooms.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">No rooms found.</div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredRooms.map((room) => (
              <div key={room.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-bold text-gray-900">{room.room_number}</h3>
                    <p className="text-sm text-gray-600">{room.room_type.replace('_', ' ')}</p>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-xs font-semibold ${room.is_active ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'}`}>
                    {room.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg bg-gray-50 p-3"><p className="text-gray-500">Floor</p><p className="font-semibold text-gray-900">{room.floor || '-'}</p></div>
                  <div className="rounded-lg bg-gray-50 p-3"><p className="text-gray-500">Capacity</p><p className="font-semibold text-gray-900">{room.capacity}</p></div>
                  <div className="rounded-lg bg-gray-50 p-3"><p className="text-gray-500">Occupied</p><p className="font-semibold text-gray-900">{room.occupied_beds}</p></div>
                  <div className="rounded-lg bg-gray-50 p-3"><p className="text-gray-500">Available</p><p className="font-semibold text-gray-900">{room.available_beds}</p></div>
                </div>
                {room.notes && <p className="mt-4 text-sm text-gray-600">{room.notes}</p>}
                <div className="mt-4 text-xs text-gray-500">Beds: {room.beds?.length || 0}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4">
          <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-4 border-b border-gray-200 pb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Add Room</h2>
                <p className="mt-1 text-sm text-gray-600">Create the room and generate beds automatically from capacity.</p>
              </div>
              <button onClick={() => setShowCreate(false)} className="rounded-full border border-gray-300 px-3 py-1 text-sm text-gray-600 hover:bg-gray-50">Close</button>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Room number" value={form.room_number} onChange={(e) => setForm((prev) => ({ ...prev, room_number: e.target.value }))} />
              <select className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900" value={form.room_type} onChange={(e) => setForm((prev) => ({ ...prev, room_type: e.target.value as RoomItem['room_type'] }))}>
                <option value="GENERAL">General</option>
                <option value="SEMI_PRIVATE">Semi Private</option>
                <option value="PRIVATE">Private</option>
                <option value="ICU">ICU</option>
                <option value="EMERGENCY">Emergency</option>
              </select>
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Floor" value={form.floor} onChange={(e) => setForm((prev) => ({ ...prev, floor: e.target.value }))} />
              <input className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Capacity" type="number" min={1} value={form.capacity} onChange={(e) => setForm((prev) => ({ ...prev, capacity: e.target.value }))} />
              <label className="flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm text-gray-700 md:col-span-2">
                <input type="checkbox" checked={form.is_active} onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.checked }))} />
                Active room
              </label>
              <textarea className="md:col-span-2 min-h-28 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500" placeholder="Notes" value={form.notes} onChange={(e) => setForm((prev) => ({ ...prev, notes: e.target.value }))} />
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={() => setShowCreate(false)} className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
              <button type="button" disabled={creating} onClick={createRoom} className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-60">
                {creating ? 'Creating...' : 'Create Room'}
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
