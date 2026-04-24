'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

function extractList(response: unknown): any[] {
  if (Array.isArray(response)) {
    return response;
  }
  if (response && typeof response === 'object' && 'results' in response) {
    const results = (response as { results?: unknown }).results;
    return Array.isArray(results) ? results : [];
  }
  return [];
}

export default function LabReportsPage() {
  const [tests, setTests] = useState<any[]>([]);
  const [bookings, setBookings] = useState<any[]>([]);
  const [results, setResults] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'tests' | 'bookings' | 'results' | 'recommendations'>('tests');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');
  const [selectedBookingDate, setSelectedBookingDate] = useState<Record<number, string>>({});
  const [bookingTestId, setBookingTestId] = useState<number | null>(null);
  const isPatient = userRole === 'PATIENT';

  useEffect(() => {
    setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
  }, []);

  const fetchLabData = useCallback(async () => {
    try {
      setIsLoading(true);
      if (activeTab === 'tests') {
        const response = await apiClient.get('/lab/tests/');
        const list = extractList(response);
        setTests(list);
        const defaults: Record<number, string> = {};
        list.forEach((test: any) => {
          if (test.available_dates && test.available_dates.length > 0) {
            defaults[test.id] = test.available_dates[0].date;
          }
        });
        setSelectedBookingDate(defaults);
      } else if (activeTab === 'bookings') {
        const response = await apiClient.get('/lab/bookings/');
        setBookings(extractList(response));
      } else if (activeTab === 'recommendations') {
        const response = await apiClient.get('/lab/recommendations/');
        setRecommendations(extractList(response));
      } else {
        const response = await apiClient.get('/lab/results/');
        setResults(extractList(response));
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load lab data');
      toast.error('Failed to load lab data');
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    void fetchLabData();
  }, [fetchLabData]);

  const handleBookTest = async (test: any) => {
    const selectedDate = selectedBookingDate[test.id];
    if (!selectedDate) {
      toast.error('Please select a booking date');
      return;
    }

    try {
      setBookingTestId(test.id);
      await apiClient.post('/lab/bookings/create/', {
        template: test.id,
        date: selectedDate,
      });
      toast.success('Lab test booked successfully');
      setActiveTab('bookings');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to book lab test');
    } finally {
      setBookingTestId(null);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Lab Tests & Reports</h1>
            <p className="mt-2 text-gray-600">
              {isPatient
                ? 'Select a test, pick an available date, and click Book Test.'
                : 'View lab bookings and test results.'}
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('tests')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'tests'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Available Tests ({tests.length})
          </button>
          <button
            onClick={() => setActiveTab('bookings')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'bookings'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Test Bookings ({bookings.length})
          </button>
          <button
            onClick={() => setActiveTab('results')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'results'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Test Results ({results.length})
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`px-4 py-2 font-medium ${
              activeTab === 'recommendations'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Recommended Tests ({recommendations.length})
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

        {/* Tests Tab */}
        {activeTab === 'tests' && !isLoading && (
          <div>
            {tests.length === 0 ? (
              <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">No available tests found</div>
            ) : (
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {tests.map((test: any) => (
                  <div key={test.id} className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">{test.name}</h3>
                        <p className="mt-1 text-sm text-gray-600">{test.description || 'No description available.'}</p>
                      </div>
                      <span className="inline-block rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-800">
                        {test.is_available ? 'Available' : 'Unavailable'}
                      </span>
                    </div>

                    <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                      <div className="rounded-lg bg-gray-50 px-3 py-2">
                        <p className="text-gray-500">Price</p>
                        <p className="font-semibold text-gray-900">₹{test.price}</p>
                      </div>
                      <div className="rounded-lg bg-gray-50 px-3 py-2">
                        <p className="text-gray-500">Duration</p>
                        <p className="font-semibold text-gray-900">{test.duration_minutes} min</p>
                      </div>
                    </div>

                    <div className="mt-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Preparation</p>
                      <p className="mt-1 text-sm text-gray-700">{test.preparation || 'No preparation instructions.'}</p>
                    </div>

                    <div className="mt-4">
                      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">Available Dates</p>
                      {test.available_dates && test.available_dates.length > 0 ? (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {test.available_dates.map((slot: any, idx: number) => (
                            <span key={`${test.id}-${idx}`} className="rounded-full bg-blue-50 px-3 py-1 text-xs text-blue-700">
                              {slot.day}: {slot.date} ({slot.start_time}-{slot.end_time})
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="mt-1 text-sm text-gray-500">No active schedule available</p>
                      )}
                    </div>

                    {isPatient && (
                      <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-gray-100 pt-4">
                        <select
                          value={selectedBookingDate[test.id] || ''}
                          onChange={(e) =>
                            setSelectedBookingDate((prev) => ({
                              ...prev,
                              [test.id]: e.target.value,
                            }))
                          }
                          className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700"
                          disabled={!test.available_dates || test.available_dates.length === 0}
                        >
                          <option value="">Select date</option>
                          {(test.available_dates || []).map((slot: any, idx: number) => (
                            <option key={`${test.id}-option-${idx}`} value={slot.date}>
                              {slot.day} - {slot.date}
                            </option>
                          ))}
                        </select>
                        <button
                          type="button"
                          onClick={() => handleBookTest(test)}
                          disabled={bookingTestId === test.id || !selectedBookingDate[test.id]}
                          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400"
                        >
                          {bookingTestId === test.id ? 'Booking...' : 'Book Test'}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Bookings Tab */}
        {activeTab === 'bookings' && !isLoading && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            {bookings.length === 0 ? (
              <div className="p-8 text-center text-gray-600">No test bookings found</div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Test Name</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Date</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Amount</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Payment</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {bookings.map((booking: any) => (
                    <tr key={booking.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{booking.template_name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{booking.date}</td>
                      <td className="px-6 py-4">
                        <span className="inline-block rounded-full px-3 py-1 text-sm bg-blue-100 text-blue-800">
                          {booking.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">₹{booking.amount}</td>
                      <td className="px-6 py-4">
                        <span className="inline-block rounded-full px-3 py-1 text-sm" style={{
                          backgroundColor: booking.payment_status === 'PAID' ? '#d1fae5' : '#fef3c7',
                          color: booking.payment_status === 'PAID' ? '#065f46' : '#92400e'
                        }}>
                          {booking.payment_status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <Link href={`/lab-reports/booking/${booking.id}`} className="text-blue-600 hover:text-blue-700 font-medium">
                          View Details
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Results Tab */}
        {activeTab === 'results' && !isLoading && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            {results.length === 0 ? (
              <div className="p-8 text-center text-gray-600">No test results found</div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Test</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Released</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Critical</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {results.map((result: any) => (
                    <tr key={result.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{result.booking_info?.template_name}</td>
                      <td className="px-6 py-4">
                        <span className="inline-block rounded-full px-3 py-1 text-sm bg-purple-100 text-purple-800">
                          {result.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {result.is_released ? '✓ Yes' : 'Pending'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-block rounded-full px-3 py-1 text-sm ${
                          result.has_critical_values 
                            ? 'bg-red-100 text-red-800' 
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {result.has_critical_values ? '⚠️ Critical' : 'Normal'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex gap-2">
                          <Link href={`/lab-reports/result/${result.id}`} className="text-blue-600 hover:text-blue-700 font-medium">
                            View Report
                          </Link>
                          {result.pdf_file && (
                            <span className="text-gray-300">|</span>
                          )}
                          {result.pdf_file ? (
                            <>
                              <a href={result.pdf_file} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-700 font-medium">
                                View PDF
                              </a>
                              <span className="text-gray-300">|</span>
                              <a href={result.pdf_file} download className="text-green-600 hover:text-green-700 font-medium">
                                Download
                              </a>
                            </>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Recommendations Tab */}
        {activeTab === 'recommendations' && !isLoading && (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            {recommendations.length === 0 ? (
              <div className="p-8 text-center text-gray-600">No recommended tests found</div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Test</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Priority</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Recommended By</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {recommendations.map((rec: any) => (
                    <tr key={rec.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{rec.test_name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{rec.priority}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{rec.status}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{rec.recommended_by_name || 'Staff'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
