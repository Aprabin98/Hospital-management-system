'use client';

import React, { Suspense, useEffect, useMemo, useState } from 'react';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';
import { useSearchParams } from 'next/navigation';

interface EligibleAppointment {
  appointment_id: number;
  doctor_id: number;
  doctor_name: string;
  date: string;
  start_time: string;
  end_time: string;
}

interface ReviewItem {
  id: number;
  appointment: number;
  appointment_date: string;
  doctor: number;
  doctor_name: string;
  rating: number;
  comment: string;
  created_at: string;
}

interface ReviewsPayload {
  eligible_appointments: EligibleAppointment[];
  reviews: ReviewItem[];
}

function ReviewsPageContent() {
  const searchParams = useSearchParams();
  const appointmentFromQuery = searchParams?.get('appointmentId');

  const [eligible, setEligible] = useState<EligibleAppointment[]>([]);
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [selectedAppointmentId, setSelectedAppointmentId] = useState<number | null>(null);
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [userRole, setUserRole] = useState('');

  const selectedAppointment = useMemo(
    () => eligible.find((item) => item.appointment_id === selectedAppointmentId) || null,
    [eligible, selectedAppointmentId]
  );

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.get<ReviewsPayload>('/reviews/');
      setEligible(data.eligible_appointments || []);
      setReviews(data.reviews || []);

      if (appointmentFromQuery) {
        const candidateId = Number(appointmentFromQuery);
        if (!Number.isNaN(candidateId) && (data.eligible_appointments || []).some((item) => item.appointment_id === candidateId)) {
          setSelectedAppointmentId(candidateId);
          return;
        }
      }

      if ((data.eligible_appointments || []).length > 0) {
        setSelectedAppointmentId(data.eligible_appointments[0].appointment_id);
      } else {
        setSelectedAppointmentId(null);
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load reviews');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchData();
  }, [appointmentFromQuery]);

  const submitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppointmentId) {
      toast.error('Please select a completed appointment to review.');
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.post('/reviews/', {
        appointment_id: selectedAppointmentId,
        rating,
        comment,
      });
      toast.success('Review submitted successfully');
      setComment('');
      setRating(5);
      await fetchData();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to submit review');
    } finally {
      setIsSaving(false);
    }
  };

  if (userRole && userRole !== 'PATIENT') {
    return (
      <MainLayout>
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <h1 className="text-xl font-semibold text-amber-900">Patient Reviews Only</h1>
          <p className="mt-2 text-sm text-amber-800">This page is designed for patients to review doctors after completed appointments.</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-gray-900">Reviews</h1>
        <p className="text-gray-600">Rate your doctor after completed appointments and track your submitted feedback.</p>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Rate Completed Appointment</h2>
            {isLoading ? (
              <p className="mt-3 text-sm text-gray-600">Loading completed appointments...</p>
            ) : eligible.length === 0 ? (
              <p className="mt-3 text-sm text-gray-600">No completed appointments available for review.</p>
            ) : (
              <form onSubmit={submitReview} className="mt-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Completed Appointment</label>
                  <select
                    value={selectedAppointmentId || ''}
                    onChange={(e) => setSelectedAppointmentId(Number(e.target.value) || null)}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                  >
                    {eligible.map((item) => (
                      <option key={item.appointment_id} value={item.appointment_id}>
                        #{item.appointment_id} - {item.doctor_name} ({item.date})
                      </option>
                    ))}
                  </select>
                </div>

                {selectedAppointment && (
                  <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-900">
                    Reviewing appointment #{selectedAppointment.appointment_id} with {selectedAppointment.doctor_name} on {selectedAppointment.date} ({selectedAppointment.start_time} - {selectedAppointment.end_time})
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700">Rating (1 to 5)</label>
                  <select
                    value={rating}
                    onChange={(e) => setRating(Number(e.target.value))}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                  >
                    {[5, 4, 3, 2, 1].map((value) => (
                      <option key={value} value={value}>
                        {value} Star{value > 1 ? 's' : ''}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Comment (optional)</label>
                  <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    rows={4}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                    placeholder="Share your consultation experience..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSaving || !selectedAppointmentId}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isSaving ? 'Submitting...' : 'Submit Review'}
                </button>
              </form>
            )}
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">My Submitted Reviews</h2>
            {isLoading ? (
              <p className="mt-3 text-sm text-gray-600">Loading reviews...</p>
            ) : reviews.length === 0 ? (
              <p className="mt-3 text-sm text-gray-600">No reviews submitted yet.</p>
            ) : (
              <div className="mt-4 space-y-3">
                {reviews.map((review) => (
                  <div key={review.id} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm font-semibold text-gray-900">{review.doctor_name || `Doctor #${review.doctor}`}</p>
                      <span className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-800">
                        {review.rating}/5
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-gray-500">Appointment #{review.appointment} on {review.appointment_date}</p>
                    <p className="mt-2 text-sm text-gray-700">{review.comment || 'No comment provided.'}</p>
                    <p className="mt-2 text-xs text-gray-500">Submitted: {new Date(review.created_at).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default function ReviewsPage() {
  return (
    <Suspense
      fallback={
        <MainLayout>
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-gray-600 shadow-sm">
            Loading reviews...
          </div>
        </MainLayout>
      }
    >
      <ReviewsPageContent />
    </Suspense>
  );
}
