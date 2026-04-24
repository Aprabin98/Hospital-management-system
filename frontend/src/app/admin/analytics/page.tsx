'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';


interface DoctorMetric {
  doctor_id: number;
  name: string;
  specialization: string;
  completed_appointments: number;
  no_show_count: number;
  no_show_rate: number;
  average_rating: number;
  total_reviews: number;
  paid_revenue: number;
}

interface AnalyticsData {
  total_appointments_month: number;
  completed_appointments_month: number;
  cancelled_appointments_month: number;
  no_show_appointments_month: number;
  pending_appointments: number;
  total_revenue_month: number;
  average_revenue_per_appointment: number;
  unique_patients_month: number;
  new_patients_month: number;
  top_specializations: Array<{ name: string; count: number }>;
  appointment_status_trend: Array<{ date: string; completed: number; cancelled: number; no_show: number }>;
  revenue_trend: Array<{ date: string; amount: number }>;
  doctor_metrics: DoctorMetric[];
}

const DEFAULT_ANALYTICS: AnalyticsData = {
  total_appointments_month: 0,
  completed_appointments_month: 0,
  cancelled_appointments_month: 0,
  no_show_appointments_month: 0,
  pending_appointments: 0,
  total_revenue_month: 0,
  average_revenue_per_appointment: 0,
  unique_patients_month: 0,
  new_patients_month: 0,
  top_specializations: [],
  appointment_status_trend: [],
  revenue_trend: [],
  doctor_metrics: [],
};

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData>(DEFAULT_ANALYTICS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<'week' | 'month' | 'quarter'>('month');

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setIsLoading(true);
        const [summary, doctorMetrics] = await Promise.all([
          apiClient.get<AnalyticsData>('/analytics/dashboard/'),
          apiClient.get<{ count: number; items: AnalyticsData['doctor_metrics'] }>('/analytics/doctor-metrics/'),
        ]);

        setAnalytics({
          ...DEFAULT_ANALYTICS,
          ...summary,
          doctor_metrics: doctorMetrics.items?.length ? doctorMetrics.items : summary.doctor_metrics || [],
        });
        setError(null);
      } catch (requestError: any) {
        setError(requestError?.message || 'Failed to load analytics');
        toast.error('Failed to load analytics');
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  const appointmentCompletionRate = useMemo(() => {
    const total = analytics.total_appointments_month;
    return total > 0 ? ((analytics.completed_appointments_month / total) * 100).toFixed(1) : 0;
  }, [analytics]);

  const cancelledRate = useMemo(() => {
    const total = analytics.total_appointments_month;
    return total > 0 ? ((analytics.cancelled_appointments_month / total) * 100).toFixed(1) : '0.0';
  }, [analytics]);

  const noShowRate = useMemo(() => {
    const total = analytics.total_appointments_month;
    return total > 0 ? ((analytics.no_show_appointments_month / total) * 100).toFixed(1) : '0.0';
  }, [analytics]);

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        {isLoading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading analytics...</div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">{error}</div>
        ) : null}
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Advanced Analytics</h1>
            <p className="mt-2 text-gray-600">Hospital performance metrics, trends, and insights</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setDateRange('week')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                dateRange === 'week'
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setDateRange('month')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                dateRange === 'month'
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Month
            </button>
            <button
              onClick={() => setDateRange('quarter')}
              className={`rounded-lg px-4 py-2 text-sm font-medium ${
                dateRange === 'quarter'
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              Quarter
            </button>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Total Appointments"
            value={analytics.total_appointments_month}
            change="+12.5%"
            icon="📅"
            color="blue"
          />
          <MetricCard
            title="Completion Rate"
            value={`${appointmentCompletionRate}%`}
            change="+2.3%"
            icon="✓"
            color="green"
          />
          <MetricCard
            title="Total Revenue"
            value={`₹${(analytics.total_revenue_month / 1000).toFixed(0)}k`}
            change="+8.7%"
            icon="💰"
            color="emerald"
          />
          <MetricCard
            title="New Patients"
            value={analytics.new_patients_month}
            change="+15.3%"
            icon="👥"
            color="purple"
          />
        </div>

        {/* Detailed Sections */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Appointment Analytics */}
          <section className="lg:col-span-2 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-gray-900">Appointment Metrics</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div className="rounded-lg bg-blue-50 p-4">
                <p className="text-sm text-gray-600">Completed</p>
                <p className="mt-1 text-2xl font-bold text-blue-900">
                  {analytics.completed_appointments_month}
                </p>
                <p className="mt-1 text-sm text-blue-700">
                  {appointmentCompletionRate}% of total
                </p>
              </div>

              <div className="rounded-lg bg-orange-50 p-4">
                <p className="text-sm text-gray-600">Cancelled</p>
                <p className="mt-1 text-2xl font-bold text-orange-900">
                  {analytics.cancelled_appointments_month}
                </p>
                <p className="mt-1 text-sm text-orange-700">
                  {cancelledRate}% of total
                </p>
              </div>

              <div className="rounded-lg bg-red-50 p-4">
                <p className="text-sm text-gray-600">No-Shows</p>
                <p className="mt-1 text-2xl font-bold text-red-900">
                  {analytics.no_show_appointments_month}
                </p>
                <p className="mt-1 text-sm text-red-700">
                  {noShowRate}% of total
                </p>
              </div>

              <div className="rounded-lg bg-yellow-50 p-4">
                <p className="text-sm text-gray-600">Pending</p>
                <p className="mt-1 text-2xl font-bold text-yellow-900">
                  {analytics.pending_appointments}
                </p>
                <p className="mt-1 text-sm text-yellow-700">
                  Awaiting confirmation
                </p>
              </div>
            </div>

            {/* Stats Table */}
            <div className="mt-6 border-t pt-6">
              <h3 className="font-semibold text-gray-900">Daily Trend (Last 5 Days)</h3>
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-2 text-left text-gray-700">Date</th>
                      <th className="px-4 py-2 text-center text-gray-700">Completed</th>
                      <th className="px-4 py-2 text-center text-gray-700">Cancelled</th>
                      <th className="px-4 py-2 text-center text-gray-700">No-Show</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {analytics.appointment_status_trend.map((item) => (
                      <tr key={item.date} className="hover:bg-gray-50">
                        <td className="px-4 py-2">{new Date(item.date).toLocaleDateString()}</td>
                        <td className="px-4 py-2 text-center">
                          <span className="inline-block rounded-full bg-green-100 px-2 py-1 text-green-800">
                            {item.completed}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span className="inline-block rounded-full bg-orange-100 px-2 py-1 text-orange-800">
                            {item.cancelled}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-center">
                          <span className="inline-block rounded-full bg-red-100 px-2 py-1 text-red-800">
                            {item.no_show}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          {/* Revenue & Patient Insights */}
          <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-xl font-bold text-gray-900">Revenue & Patients</h2>
            <div className="mt-6 space-y-4">
              <div className="rounded-lg bg-gradient-to-br from-emerald-50 to-emerald-100 p-4">
                <p className="text-sm text-gray-600">Monthly Revenue</p>
                <p className="mt-1 text-2xl font-bold text-emerald-900">
                  ₹{(analytics.total_revenue_month / 1000).toFixed(1)}k
                </p>
                <p className="mt-2 text-xs text-emerald-700">
                  Avg per appointment: ₹{analytics.average_revenue_per_appointment}
                </p>
              </div>

              <div className="rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 p-4">
                <p className="text-sm text-gray-600">Unique Patients</p>
                <p className="mt-1 text-2xl font-bold text-blue-900">
                  {analytics.unique_patients_month}
                </p>
                <p className="mt-2 text-xs text-blue-700">
                  New this month: {analytics.new_patients_month}
                </p>
              </div>

              <div className="rounded-lg border border-gray-200 p-4">
                <h3 className="font-semibold text-gray-900">Top Specializations</h3>
                <div className="mt-3 space-y-2">
                  {analytics.top_specializations.map((spec) => (
                    <div key={spec.name} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700">{spec.name}</span>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-16 rounded-full bg-gray-200">
                          <div
                            className="h-full rounded-full bg-blue-600"
                            style={{
                              width: `${(spec.count / 50) * 100}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm font-medium text-gray-900">{spec.count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Doctor Performance */}
        <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-bold text-gray-900">Top Performing Doctors</h2>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Doctor</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Appointments</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">No-Shows</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Rating</th>
                  <th className="px-6 py-3 text-center text-sm font-semibold text-gray-700">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {analytics.doctor_metrics.map((doctor) => (
                  <tr key={doctor.doctor_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">{doctor.name}</p>
                        <p className="text-sm text-gray-500">{doctor.specialization}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="font-medium text-gray-900">{doctor.completed_appointments}</span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="inline-block rounded-full bg-red-100 px-3 py-1 text-sm text-red-800">
                        {doctor.no_show_count} ({doctor.no_show_rate.toFixed(1)}%)
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <span className="text-lg">⭐</span>
                        <span className="font-medium text-gray-900">{doctor.average_rating}</span>
                        <span className="text-sm text-gray-500">({doctor.total_reviews})</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className="font-medium text-emerald-700">₹{(doctor.paid_revenue / 1000).toFixed(0)}k</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </MainLayout>
  );
}

interface MetricCardProps {
  title: string;
  value: string | number;
  change: string;
  icon: string;
  color: 'blue' | 'green' | 'emerald' | 'purple' | 'red' | 'orange' | 'yellow';
}

function MetricCard({ title, value, change, icon, color }: MetricCardProps) {
  const colorClasses: { [key: string]: string } = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    emerald: 'bg-emerald-50 text-emerald-700',
    purple: 'bg-purple-50 text-purple-700',
    red: 'bg-red-50 text-red-700',
    orange: 'bg-orange-50 text-orange-700',
    yellow: 'bg-yellow-50 text-yellow-700',
  };

  return (
    <div className={`rounded-lg p-6 shadow-sm ${colorClasses[color]}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-700">{title}</p>
          <p className="mt-2 text-2xl font-bold">{value}</p>
          <p className="mt-1 text-sm font-medium text-green-700">{change}</p>
        </div>
        <div className="text-3xl">{icon}</div>
      </div>
    </div>
  );
}
