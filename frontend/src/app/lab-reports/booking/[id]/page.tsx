'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

export default function BookingDetailsPage() {
  const params = useParams<{ id?: string | string[] }>();
  const bookingId = typeof params?.id === 'string' ? params.id : '';
  const [booking, setBooking] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBookingDetails = useCallback(async () => {
    if (!bookingId) {
      setError('Invalid booking id');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiClient.get(`/lab/bookings/${bookingId}/`);
      setBooking(response);
    } catch (err: any) {
      setError(err?.message || 'Failed to load booking details');
      toast.error('Failed to load booking details');
    } finally {
      setIsLoading(false);
    }
  }, [bookingId]);

  useEffect(() => {
    void fetchBookingDetails();
  }, [fetchBookingDetails]);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </MainLayout>
    );
  }

  if (error || !booking) {
    return (
      <MainLayout>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          {error || 'Booking not found'}
        </div>
        <Link href="/lab-reports" className="mt-4 inline-block text-blue-600 hover:text-blue-700">
          ← Back to Lab Reports
        </Link>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Link href="/lab-reports" className="text-blue-600 hover:text-blue-700 font-medium mb-2 inline-block">
              ← Back to Lab Reports
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Test Booking Details</h1>
            <p className="mt-2 text-gray-600">View your test booking information</p>
          </div>
        </div>

        {/* Status Alert */}
        <div className={`rounded-lg border px-6 py-4 ${
          booking.status === 'COMPLETED' 
            ? 'border-green-200 bg-green-50 text-green-700'
            : booking.status === 'CANCELLED'
            ? 'border-red-200 bg-red-50 text-red-700'
            : 'border-blue-200 bg-blue-50 text-blue-700'
        }`}>
          <p className="font-medium">Booking Status: {booking.status}</p>
        </div>

        {/* Main Details */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6 space-y-4">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Booking Information</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-600">Test Name</p>
              <p className="text-lg font-semibold text-gray-900">{booking.template_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Booking Date</p>
              <p className="text-lg font-semibold text-gray-900">{booking.booking_date || booking.date}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Test Date</p>
              <p className="text-lg font-semibold text-gray-900">{booking.date}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Time</p>
              <p className="text-lg font-semibold text-gray-900">{booking.time || 'Not scheduled'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Amount</p>
              <p className="text-lg font-semibold text-gray-900">₹{booking.amount}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Payment Status</p>
              <p className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${
                booking.payment_status === 'PAID'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {booking.payment_status}
              </p>
            </div>
          </div>
        </div>

        {/* Additional Information */}
        {booking.notes && (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Notes</h2>
            <p className="text-gray-700">{booking.notes}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <Link 
            href="/lab-reports"
            className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
          >
            Back to Lab Reports
          </Link>
        </div>
      </div>
    </MainLayout>
  );
}
