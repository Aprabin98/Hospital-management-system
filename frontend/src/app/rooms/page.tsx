'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

export default function RoomsPage() {
  const [currentAssignment, setCurrentAssignment] = useState<any>(null);
  const [assignments, setAssignments] = useState<any[]>([]);
  const [availableRooms, setAvailableRooms] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'current' | 'history' | 'available'>('current');
  const [isLoading, setIsLoading] = useState(true);
  const [isBookingRoomId, setIsBookingRoomId] = useState<number | null>(null);
  const [userRole, setUserRole] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchRoomData = useCallback(async () => {
    try {
      setIsLoading(true);
      
      if (activeTab === 'current') {
        try {
          const response = await apiClient.get('/rooms/current-assignment/');
          setCurrentAssignment(response);
        } catch (e) {
          setCurrentAssignment(null);
        }
      } else if (activeTab === 'history') {
        const response = await apiClient.get('/rooms/assignments/');
        setAssignments(response.results || []);
      } else if (activeTab === 'available') {
        const response = await apiClient.get('/rooms/available/');
        setAvailableRooms(Array.isArray(response) ? response : response.results || []);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load room data');
      toast.error('Failed to load room data');
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    void fetchRoomData();
  }, [fetchRoomData]);

  const isPatient = userRole === 'PATIENT';

  const handleBookRoom = async (roomId: number) => {
    try {
      setIsBookingRoomId(roomId);
      await apiClient.post('/rooms/book-request/', { room: roomId });
      toast.success('Room booking request submitted. Reception will process it.');
      setActiveTab('current');
      await fetchRoomData();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to submit room booking request');
    } finally {
      setIsBookingRoomId(null);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Room Allocation</h1>
            <p className="mt-2 text-gray-600">View your room assignments and availability</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('current')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'current'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Current Assignment
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'history'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Assignment History
          </button>
          <button
            onClick={() => setActiveTab('available')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'available'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Available Rooms
          </button>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg text-gray-600">Loading...</div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Current Assignment Tab */}
        {activeTab === 'current' && !isLoading && (
          <div>
            {currentAssignment ? (
              <div className="rounded-lg border border-green-200 bg-green-50 p-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <p className="text-sm text-gray-600">Room Details</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      {currentAssignment.room_info?.room_number}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {currentAssignment.room_info?.room_type} • Floor {currentAssignment.room_info?.floor}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Bed Details</p>
                    <p className="text-2xl font-bold text-gray-900 mt-1">
                      Bed {currentAssignment.bed_info?.bed_number}
                    </p>
                    <p className="text-sm text-gray-600 mt-1">
                      {currentAssignment.status}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-600">Doctor in Charge</p>
                    <p className="text-lg font-semibold text-gray-900 mt-1">
                      {currentAssignment.doctor_name || 'N/A'}
                    </p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-sm text-gray-600">Admitted Since</p>
                    <p className="text-sm text-gray-900 mt-1">
                      {new Date(currentAssignment.admitted_at).toLocaleDateString()} {new Date(currentAssignment.admitted_at).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
                <p className="text-gray-600">No current room assignment</p>
              </div>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && !isLoading && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            {assignments.length === 0 ? (
              <div className="p-8 text-center text-gray-600">No assignment history</div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Room</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Bed</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Admitted</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Discharged</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {assignments.map((assignment: any) => (
                    <tr key={assignment.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{assignment.room_info?.room_number}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">Bed {assignment.bed_info?.bed_number}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(assignment.admitted_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {assignment.discharged_at ? new Date(assignment.discharged_at).toLocaleDateString() : '-'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-block rounded-full px-3 py-1 text-sm ${
                          assignment.status === 'DISCHARGED' ? 'bg-gray-100 text-gray-800' : 'bg-blue-100 text-blue-800'
                        }`}>
                          {assignment.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Available Rooms Tab */}
        {activeTab === 'available' && !isLoading && (
          <div className="space-y-6">
            {isPatient && currentAssignment && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                You are already admitted and cannot book another room until discharged.
              </div>
            )}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {availableRooms.length === 0 ? (
                <div className="col-span-full rounded-lg border border-gray-200 bg-white p-8 text-center">
                  <p className="text-gray-600">No available rooms</p>
                </div>
              ) : (
                availableRooms.map((room: any) => {
                  const availableBeds = (room.beds || []).filter((b: any) => b.status === 'AVAILABLE');
                  return (
                    <div key={room.id} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-lg font-bold text-gray-900">{room.room_number}</h3>
                          <p className="text-sm text-gray-600">{room.room_type}</p>
                        </div>
                        <span className="text-2xl">🏥</span>
                      </div>

                      <div className="space-y-2 text-sm mb-4 p-3 bg-gray-50 rounded">
                        <p><span className="text-gray-600">Floor:</span> <span className="font-medium">{room.floor || 'N/A'}</span></p>
                        <p><span className="text-gray-600">Capacity:</span> <span className="font-medium">{room.capacity}</span></p>
                        <p><span className="text-gray-600">Available:</span> <span className="font-medium text-green-700">{room.available_beds}</span></p>
                        <p><span className="text-gray-600">Occupied:</span> <span className="font-medium text-red-700">{room.occupied_beds}</span></p>
                      </div>

                      {availableBeds.length > 0 ? (
                        <div className="space-y-2">
                          {availableBeds.map((bed: any) => (
                            <div
                              key={bed.id}
                              className="w-full rounded-lg border border-blue-300 bg-blue-50 px-3 py-2 text-sm font-medium text-blue-700"
                            >
                              Available Bed {bed.bed_number}
                            </div>
                          ))}

                          {isPatient && (
                            <button
                              type="button"
                              onClick={() => handleBookRoom(room.id)}
                              disabled={Boolean(currentAssignment) || isBookingRoomId === room.id}
                              className="mt-2 w-full rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
                            >
                              {isBookingRoomId === room.id ? 'Submitting...' : 'Book This Room'}
                            </button>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500">No available beds in this room.</p>
                      )}

                      {room.notes && (
                        <p className="text-xs text-gray-600 mt-3">{room.notes}</p>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
