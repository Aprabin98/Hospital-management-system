'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

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
  reviews: ReviewItem[];
}

export default function MyRatingsPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userRole, setUserRole] = useState('');

  useEffect(() => {
    const role = (localStorage.getItem('userRole') || '').toUpperCase();
    setUserRole(role);

    const run = async () => {
      try {
        setIsLoading(true);
        const data = await apiClient.get<ReviewsPayload>('/reviews/');
        setReviews(data.reviews || []);
      } catch (err: any) {
        toast.error(err?.message || 'Failed to load rating summary');
      } finally {
        setIsLoading(false);
      }
    };

    run();
  }, []);

  const averageRating = useMemo(() => {
    if (!reviews.length) return 0;
    const total = reviews.reduce((sum, item) => sum + item.rating, 0);
    return total / reviews.length;
  }, [reviews]);

  const ratingBreakdown = useMemo(() => {
    const seed: Record<number, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
    reviews.forEach((item) => {
      seed[item.rating] = (seed[item.rating] || 0) + 1;
    });
    return seed;
  }, [reviews]);

  if (userRole && userRole !== 'PATIENT') {
    return (
      <MainLayout>
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6">
          <h1 className="text-xl font-semibold text-amber-900">Patient Ratings Only</h1>
          <p className="mt-2 text-sm text-amber-800">This page is available for patient accounts only.</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Ratings</h1>
            <p className="mt-1 text-gray-600">Summary of ratings you submitted for doctors.</p>
          </div>
          <Link
            href="/reviews"
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Write New Review
          </Link>
        </div>

        <div className="rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          Note: Use the Reviews page to submit new feedback after completed appointments.
        </div>

        {isLoading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">
            Loading rating summary...
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 p-4 text-white">
                <p className="text-sm opacity-90">Average Rating</p>
                <p className="mt-1 text-3xl font-bold">{averageRating.toFixed(1)} / 5</p>
              </div>
              <div className="rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 p-4 text-white">
                <p className="text-sm opacity-90">Total Reviews</p>
                <p className="mt-1 text-3xl font-bold">{reviews.length}</p>
              </div>
              <div className="rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 p-4 text-white">
                <p className="text-sm opacity-90">5-Star Reviews</p>
                <p className="mt-1 text-3xl font-bold">{ratingBreakdown[5]}</p>
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">Rating Breakdown</h2>
              <div className="mt-4 space-y-2">
                {[5, 4, 3, 2, 1].map((score) => {
                  const count = ratingBreakdown[score] || 0;
                  const width = reviews.length ? (count / reviews.length) * 100 : 0;
                  return (
                    <div key={score} className="flex items-center gap-3">
                      <span className="w-14 text-sm font-medium text-gray-700">{score} star</span>
                      <div className="h-2 flex-1 rounded bg-gray-100">
                        <div className="h-2 rounded bg-amber-500" style={{ width: `${width}%` }} />
                      </div>
                      <span className="w-8 text-right text-sm text-gray-600">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900">Recent Reviews</h2>
              {reviews.length === 0 ? (
                <p className="mt-3 text-sm text-gray-600">You have not submitted any reviews yet.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {reviews.slice(0, 10).map((review) => (
                    <div key={review.id} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-sm font-semibold text-gray-900">{review.doctor_name || `Doctor #${review.doctor}`}</p>
                        <span className="rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-800">
                          {review.rating}/5
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-gray-500">Appointment #{review.appointment} on {review.appointment_date}</p>
                      <p className="mt-2 text-sm text-gray-700">{review.comment || 'No comment provided.'}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
}
