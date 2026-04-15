'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface DashboardStats {
  total_patients: number;
  total_appointments: number;
  pending_appointments: number;
  total_doctors: number;
}

interface RevenueSummary {
  total_revenue: number;
  total_transactions: number;
  total_refunded_amount: number;
  pending_refund_count: number;
  net_revenue: number;
}

type ReportCategory = 'ALL' | 'OPERATIONS' | 'FINANCE' | 'CLINICAL' | 'AI' | 'COMPLIANCE';

interface ReportLinkCard {
  title: string;
  href: string;
  className: string;
  category: ReportCategory;
}

export default function ReportsPage() {
  const [role] = useState(() => {
    if (typeof window === 'undefined') {
      return '';
    }
    return (localStorage.getItem('userRole') || '').toUpperCase();
  });
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null);
  const [category, setCategory] = useState<ReportCategory>('ALL');

  const isDoctor = role === 'DOCTOR';
  const isAdmin = role === 'ADMIN';
  const isReceptionist = role === 'RECEPTIONIST';

  const reportCards = useMemo<ReportLinkCard[]>(() => [
    {
      title: 'Billing Operations Report',
      href: '/billing',
      className: 'rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-indigo-700 hover:bg-indigo-100',
      category: 'FINANCE',
    },
    {
      title: 'Appointment Load Report',
      href: '/appointments?filter=ACTIVE',
      className: 'rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-blue-700 hover:bg-blue-100',
      category: 'OPERATIONS',
    },
    {
      title: 'Room Occupancy Report',
      href: '/rooms',
      className: 'rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-700 hover:bg-emerald-100',
      category: 'OPERATIONS',
    },
    {
      title: 'Patient Registry Report',
      href: '/patients',
      className: 'rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 hover:bg-slate-100',
      category: 'CLINICAL',
    },
    {
      title: 'Audit Log Report',
      href: '/audit-logs',
      className: 'rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 hover:bg-rose-100',
      category: 'COMPLIANCE',
    },
    {
      title: 'AI Report Reader',
      href: '/ai-health/report-reader',
      className: 'rounded-lg border border-cyan-200 bg-cyan-50 px-4 py-3 text-cyan-700 hover:bg-cyan-100',
      category: 'AI',
    },
    {
      title: 'AI Triage',
      href: '/ai-health/triage',
      className: 'rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-700 hover:bg-green-100',
      category: 'AI',
    },
    {
      title: 'Heart Risk Detector',
      href: '/ai-health/heart-risk',
      className: 'rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 hover:bg-rose-100',
      category: 'CLINICAL',
    },
    {
      title: 'Issued Prescriptions',
      href: '/prescriptions-writer',
      className: 'rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-800 hover:bg-gray-50',
      category: 'CLINICAL',
    },
  ], []);

  const filteredReportCards = reportCards.filter((item) => category === 'ALL' || item.category === category);

  useEffect(() => {
    const fetchStats = async () => {
      if (!role) {
        return;
      }

      try {
        const dashboardStats = await apiClient.get<DashboardStats>('/dashboard/stats/');
        setStats(dashboardStats);

        if (role === 'ADMIN') {
          const revenueSummary = await apiClient.get<RevenueSummary>('/payments/revenue/');
          setRevenue(revenueSummary);
        }
      } catch {
        setStats(null);
        setRevenue(null);
      }
    };

    fetchStats();
  }, [role]);

  return (
    <MainLayout>
      <div className="space-y-4">
        <h1 className="text-3xl font-bold text-gray-900">Operational Reports</h1>
        <p className="text-gray-600">Use role-specific report modules and operational dashboards.</p>

        <div className="flex flex-wrap gap-2 rounded-xl border border-gray-200 bg-white p-3 shadow-sm">
          {(['ALL', 'OPERATIONS', 'FINANCE', 'CLINICAL', 'AI', 'COMPLIANCE'] as ReportCategory[]).map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setCategory(item)}
              className={`rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-wide ${
                category === item
                  ? 'bg-blue-600 text-white'
                  : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              {item.toLowerCase()}
            </button>
          ))}
        </div>

        {stats && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 p-4 text-white shadow-sm">
              <p className="text-sm opacity-85">Patients</p>
              <p className="mt-2 text-2xl font-bold">{stats.total_patients}</p>
            </div>
            <div className="rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 p-4 text-white shadow-sm">
              <p className="text-sm opacity-85">Appointments</p>
              <p className="mt-2 text-2xl font-bold">{stats.total_appointments}</p>
            </div>
            <div className="rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 p-4 text-white shadow-sm">
              <p className="text-sm opacity-85">Pending Workload</p>
              <p className="mt-2 text-2xl font-bold">{stats.pending_appointments}</p>
            </div>
            <div className="rounded-xl bg-gradient-to-br from-slate-600 to-gray-700 p-4 text-white shadow-sm">
              <p className="text-sm opacity-85">Doctors</p>
              <p className="mt-2 text-2xl font-bold">{stats.total_doctors}</p>
            </div>
          </div>
        )}

        {isAdmin && revenue && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-gray-500">Net Revenue</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">Rs. {Number(revenue.net_revenue).toFixed(2)}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-gray-500">Refunded Amount</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">Rs. {Number(revenue.total_refunded_amount).toFixed(2)}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-gray-500">Pending Refund Requests</p>
              <p className="mt-1 text-2xl font-bold text-gray-900">{revenue.pending_refund_count}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filteredReportCards.map((card) => {
            if (card.category === 'FINANCE' && !(isAdmin || isReceptionist)) {
              return null;
            }
            if (card.category === 'OPERATIONS' && !(isAdmin || isReceptionist)) {
              return null;
            }
            if (card.category === 'CLINICAL' && !(isAdmin || isReceptionist || isDoctor)) {
              return null;
            }
            if (card.category === 'COMPLIANCE' && !isAdmin) {
              return null;
            }
            return (
              <Link key={card.title} href={card.href} className={card.className}>
                {card.title}
              </Link>
            );
          })}
        </div>
      </div>
    </MainLayout>
  );
}
