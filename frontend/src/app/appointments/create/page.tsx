'use client';

import React, { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

interface Doctor {
  id: number;
  user: {
    first_name: string;
    last_name: string;
    username: string;
  };
  specialization: {
    id: number;
    name: string;
  };
  consultation_fee: number;
}

interface SlotResponse {
  is_on_leave: boolean;
  schedule: {
    shift_name: string | null;
    start_time: string | null;
    end_time: string | null;
    slot_duration: number | null;
  };
  slots: Array<{ start: string; end: string }>;
}

function CreateAppointmentPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const doctorId = searchParams?.get('doctor');

  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<number | null>(doctorId ? parseInt(doctorId) : null);
  const [appointmentDate, setAppointmentDate] = useState('');
  const [appointmentTime, setAppointmentTime] = useState('');
  const [notes, setNotes] = useState('');
  const [slots, setSlots] = useState<Array<{ start: string; end: string }>>([]);
  const [scheduleInfo, setScheduleInfo] = useState<SlotResponse['schedule'] | null>(null);
  const [isDoctorOnLeave, setIsDoctorOnLeave] = useState(false);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingDoctors, setIsLoadingDoctors] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    fetchDoctors();
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
  }, []);

  useEffect(() => {
    setAppointmentTime('');
    if (!selectedDoctor || !appointmentDate) {
      setSlots([]);
      setScheduleInfo(null);
      setIsDoctorOnLeave(false);
      return;
    }

    const fetchSlots = async () => {
      try {
        setIsLoadingSlots(true);
        const response = await apiClient.get<SlotResponse>(
          `/appointments/available-slots/?doctor_id=${selectedDoctor}&date=${appointmentDate}`
        );
        setSlots(response.slots || []);
        setScheduleInfo(response.schedule || null);
        setIsDoctorOnLeave(Boolean(response.is_on_leave));
      } catch (err: any) {
        setSlots([]);
        setScheduleInfo(null);
        setIsDoctorOnLeave(false);
        toast.error(err?.message || 'Failed to load available slots');
      } finally {
        setIsLoadingSlots(false);
      }
    };

    fetchSlots();
  }, [selectedDoctor, appointmentDate]);

  const fetchDoctors = async () => {
    try {
      setIsLoadingDoctors(true);
      const response = await apiClient.get<{ results: Doctor[] }>('/doctors/');
      setDoctors(response.results || []);
    } catch (err: any) {
      setError('Failed to load doctors');
      toast.error('Failed to load doctors');
    } finally {
      setIsLoadingDoctors(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedDoctor || !appointmentDate || !appointmentTime) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      setIsLoading(true);
      const selectedSlot = slots.find((slot) => slot.start === appointmentTime);
      if (!selectedSlot) {
        toast.error('Please choose a valid available slot');
        setIsLoading(false);
        return;
      }

      const response = await apiClient.post<{ id: number }>('/appointments/create/', {
        doctor: selectedDoctor,
        date: appointmentDate,
        start_time: selectedSlot.start,
        end_time: selectedSlot.end,
        notes: notes,
      });

      toast.success('Appointment created successfully!');
      router.push(`/appointments/${response.id}`);
    } catch (err: any) {
      const errorMsg = err?.message || 'Failed to create appointment';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedDoctorInfo = doctors.find(d => d.id === selectedDoctor);
  const today = new Date().toISOString().split('T')[0];

  if (userRole === 'DOCTOR') {
    return (
      <MainLayout>
        <div className="max-w-2xl rounded-lg border border-amber-200 bg-amber-50 p-6">
          <h1 className="text-xl font-bold text-amber-900">Booking Not Allowed for Doctor Role</h1>
          <p className="mt-2 text-sm text-amber-800">
            Doctors should not create appointments for themselves from this page. Appointments are created by patients or reception/admin.
          </p>
          <Link
            href="/appointments"
            className="mt-4 inline-block rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-700"
          >
            Back to Appointments
          </Link>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Link href="/appointments" className="text-blue-600 hover:text-blue-700 font-medium mb-2 inline-block">
              ← Back to Appointments
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Book New Appointment</h1>
            <p className="mt-2 text-gray-600">Schedule an appointment with a doctor</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form Section */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="rounded-lg border border-gray-200 bg-white shadow-sm p-6 space-y-6">
              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
                  {error}
                </div>
              )}

              {/* Doctor Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Doctor *
                </label>
                {isLoadingDoctors ? (
                  <div className="text-gray-600">Loading doctors...</div>
                ) : (
                  <select
                    value={selectedDoctor || ''}
                    onChange={(e) => setSelectedDoctor(parseInt(e.target.value) || null)}
                    required
                    className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Choose a doctor</option>
                    {doctors.map((doctor) => (
                      <option key={doctor.id} value={doctor.id}>
                        Dr. {doctor.user.first_name || doctor.user.username} - {doctor.specialization.name}
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Appointment Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Appointment Date *
                </label>
                <input
                  type="date"
                  value={appointmentDate}
                  onChange={(e) => setAppointmentDate(e.target.value)}
                  min={today}
                  required
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              {/* Working Schedule */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Doctor Working Schedule
                </label>
                {!selectedDoctor || !appointmentDate ? (
                  <p className="text-sm text-gray-500">Select doctor and date to view schedule.</p>
                ) : isLoadingSlots ? (
                  <p className="text-sm text-gray-500">Loading available slots...</p>
                ) : isDoctorOnLeave ? (
                  <p className="text-sm text-red-600">Doctor is on leave for this date.</p>
                ) : !scheduleInfo?.shift_name ? (
                  <p className="text-sm text-red-600">No active schedule for this day.</p>
                ) : (
                  <div className="rounded-lg border border-gray-200 bg-gray-50 p-3">
                    <p className="text-sm font-medium text-gray-800">{scheduleInfo.shift_name} Shift</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {scheduleInfo.start_time} - {scheduleInfo.end_time} ({scheduleInfo.slot_duration} min slots)
                    </p>
                  </div>
                )}
              </div>

              {/* Appointment Time Slot */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Available Time Slots *
                </label>
                {!selectedDoctor || !appointmentDate ? (
                  <p className="text-sm text-gray-500">Select doctor and date first.</p>
                ) : slots.length === 0 ? (
                  <p className="text-sm text-gray-500">No slots available for this date.</p>
                ) : (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {slots.map((slot) => {
                      const selected = appointmentTime === slot.start;
                      return (
                        <button
                          key={`${slot.start}-${slot.end}`}
                          type="button"
                          onClick={() => setAppointmentTime(slot.start)}
                          className={`rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                            selected
                              ? 'border-blue-600 bg-blue-600 text-white'
                              : 'border-gray-300 bg-white text-gray-900 hover:border-blue-400'
                          }`}
                        >
                          {slot.start}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Additional Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Additional Notes
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Any additional information or medical history..."
                  rows={4}
                  className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 focus:ring-blue-500"
                />
              </div>

              {/* Submit Buttons */}
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="flex-1 rounded-lg bg-blue-600 text-white font-medium py-2 hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {isLoading ? 'Booking...' : 'Confirm Appointment'}
                </button>
                <Link
                  href="/appointments"
                  className="flex-1 rounded-lg border border-gray-300 text-gray-700 font-medium py-2 hover:bg-gray-50 transition-colors text-center"
                >
                  Cancel
                </Link>
              </div>
            </form>
          </div>

          {/* Summary Section */}
          <div className="lg:col-span-1">
            <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6 sticky top-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Appointment Summary</h3>
              
              {selectedDoctorInfo && (
                <div className="space-y-4 pb-4 border-b border-gray-200">
                  <div>
                    <p className="text-xs text-gray-600">Doctor</p>
                    <p className="font-semibold text-gray-900">
                      Dr. {selectedDoctorInfo.user.first_name || selectedDoctorInfo.user.username}
                    </p>
                    <p className="text-sm text-blue-600">{selectedDoctorInfo.specialization.name}</p>
                  </div>

                  <div>
                    <p className="text-xs text-gray-600">Consultation Fee</p>
                    <p className="text-2xl font-bold text-gray-900">₹{selectedDoctorInfo.consultation_fee}</p>
                  </div>
                </div>
              )}

              {appointmentDate && (
                <div className="space-y-4 pb-4 border-b border-gray-200">
                  <div>
                    <p className="text-xs text-gray-600">Date</p>
                    <p className="font-semibold text-gray-900">
                      {new Date(appointmentDate).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                  </div>

                  {appointmentTime && (
                    <div>
                      <p className="text-xs text-gray-600">Time</p>
                      <p className="font-semibold text-gray-900">{appointmentTime}</p>
                    </div>
                  )}

                  {scheduleInfo?.shift_name && (
                    <div>
                      <p className="text-xs text-gray-600">Shift</p>
                      <p className="font-semibold text-gray-900">{scheduleInfo.shift_name}</p>
                    </div>
                  )}
                </div>
              )}

              <div className="pt-4">
                <p className="text-xs text-gray-600 mb-2">Important Notes:</p>
                <ul className="text-xs text-gray-600 space-y-1 list-disc list-inside">
                  <li>Please arrive 10 minutes early</li>
                  <li>Bring your insurance card if applicable</li>
                  <li>Confirmation will be sent to your email</li>
                  <li>You can cancel or reschedule 24 hours before appointment</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default function CreateAppointmentPage() {
  return (
    <Suspense
      fallback={
        <MainLayout>
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-gray-600 shadow-sm">
            Loading appointment booking...
          </div>
        </MainLayout>
      }
    >
      <CreateAppointmentPageContent />
    </Suspense>
  );
}
