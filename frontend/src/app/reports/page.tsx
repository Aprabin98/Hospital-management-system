'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';
import { useAuth } from '@/hooks';

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
  allowedRoles: string[];
}

interface ExportAction {
  id: string;
  title: string;
  description: string;
  format: 'CSV' | 'JSON';
  allowedRoles: string[];
  run: () => Promise<void>;
}

export default function ReportsPage() {
  const { userRole, isLoading: authLoading } = useAuth();
  const role = (userRole || '').toUpperCase();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [revenue, setRevenue] = useState<RevenueSummary | null>(null);
  const [category, setCategory] = useState<ReportCategory>('ALL');
  const [exportMessage, setExportMessage] = useState('');
  const [activeExportId, setActiveExportId] = useState('');

  const isDoctor = role === 'DOCTOR';
  const isAdmin = role === 'ADMIN';
  const isReceptionist = role === 'RECEPTIONIST';
  const isFinanceRole = ['ADMIN', 'BILLING_OFFICER', 'INSURANCE_COORDINATOR'].includes(role);
  const isComplianceRole = ['ADMIN', 'QUALITY_COMPLIANCE_OFFICER'].includes(role);

  const reportCards = useMemo<ReportLinkCard[]>(() => [
    {
      title: 'Billing Operations Report',
      href: '/billing',
      className: 'rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-indigo-700 hover:bg-indigo-100',
      category: 'FINANCE',
      allowedRoles: ['ADMIN', 'RECEPTIONIST', 'PATIENT'],
    },
    {
      title: 'Appointment Load Report',
      href: '/appointments?filter=ACTIVE',
      className: 'rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-blue-700 hover:bg-blue-100',
      category: 'OPERATIONS',
      allowedRoles: ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'NURSE'],
    },
    {
      title: 'Room Occupancy Report',
      href: '/rooms',
      className: 'rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-emerald-700 hover:bg-emerald-100',
      category: 'OPERATIONS',
      allowedRoles: ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'PATIENT'],
    },
    {
      title: 'Patient Registry Report',
      href: '/patients',
      className: 'rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-slate-700 hover:bg-slate-100',
      category: 'CLINICAL',
      allowedRoles: ['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'NURSE'],
    },
    {
      title: 'Audit Log Report',
      href: '/audit-logs',
      className: 'rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 hover:bg-rose-100',
      category: 'COMPLIANCE',
      allowedRoles: ['ADMIN'],
    },
    {
      title: 'AI Report Reader',
      href: '/ai-health/report-reader',
      className: 'rounded-lg border border-cyan-200 bg-cyan-50 px-4 py-3 text-cyan-700 hover:bg-cyan-100',
      category: 'AI',
      allowedRoles: ['DOCTOR', 'PATIENT', 'RECEPTIONIST'],
    },
    {
      title: 'AI Triage',
      href: '/ai-health/triage',
      className: 'rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-700 hover:bg-green-100',
      category: 'AI',
      allowedRoles: ['DOCTOR', 'PATIENT', 'RECEPTIONIST', 'NURSE'],
    },
    {
      title: 'Heart Risk Detector',
      href: '/ai-health/heart-risk',
      className: 'rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-rose-700 hover:bg-rose-100',
      category: 'CLINICAL',
      allowedRoles: ['DOCTOR', 'PATIENT'],
    },
    {
      title: 'Issued Prescriptions',
      href: '/prescriptions-writer',
      className: 'rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-800 hover:bg-gray-50',
      category: 'CLINICAL',
      allowedRoles: ['DOCTOR'],
    },
  ], []);

  const filteredReportCards = reportCards.filter(
    (item) => item.allowedRoles.includes(role) && (category === 'ALL' || item.category === category)
  );

  const saveBlob = (blob: Blob, fileName: string) => {
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = objectUrl;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(objectUrl);
  };

  const downloadCsv = useCallback(async (path: string, fileName: string) => {
    const token = localStorage.getItem('authToken') || localStorage.getItem('token');
    if (!token) {
      throw new Error('Authentication token not found. Please sign in again.');
    }

    const apiBase = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
    const response = await fetch(`${apiBase}${path}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to export CSV (${response.status}).`);
    }

    const blob = await response.blob();
    saveBlob(blob, fileName);
  }, []);

  const downloadJson = useCallback(async (path: string, fileName: string) => {
    const payload = await apiClient.get(path);
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    saveBlob(blob, fileName);
  }, []);

  const runExport = async (actionId: string, run: () => Promise<void>) => {
    try {
      setActiveExportId(actionId);
      setExportMessage('Generating report export...');
      await run();
      setExportMessage('Report exported successfully.');
    } catch {
      setExportMessage('Report export failed. Please verify permissions and try again.');
    } finally {
      setActiveExportId('');
    }
  };

  const exportActions: ExportAction[] = useMemo(() => [
    {
      id: 'room-csv',
      title: 'Room Occupancy Snapshot',
      description: 'Download the latest room statistics as CSV.',
      format: 'CSV',
      allowedRoles: ['ADMIN', 'RECEPTIONIST'],
      run: () => downloadCsv('/rooms/statistics/export/csv/', `room-occupancy-${new Date().toISOString().slice(0, 10)}.csv`),
    },
    {
      id: 'finance-daily',
      title: 'Daily Finance Reconciliation',
      description: 'Export finance reconciliation metrics as JSON.',
      format: 'JSON',
      allowedRoles: ['ADMIN', 'BILLING_OFFICER', 'INSURANCE_COORDINATOR'],
      run: () => downloadJson('/finance/reconciliation/daily/', `finance-reconciliation-${new Date().toISOString().slice(0, 10)}.json`),
    },
    {
      id: 'compliance-evidence',
      title: 'Compliance Evidence Pack',
      description: 'Export compliance incidents, breaches, and drill evidence.',
      format: 'JSON',
      allowedRoles: ['ADMIN', 'QUALITY_COMPLIANCE_OFFICER'],
      run: () => downloadJson('/compliance/evidence-export/', `compliance-evidence-${new Date().toISOString().slice(0, 10)}.json`),
    },
  ], [downloadCsv, downloadJson]);

  const visibleExportActions = exportActions.filter((action) => action.allowedRoles.includes(role));

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
        <PageHeader
          title="Operational Reports"
          description="Use role-specific report modules and operational dashboards."
        />

        {authLoading ? <p className="text-sm text-gray-600">Loading reports workspace...</p> : null}

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
            <StatCard label="Patients" value={stats.total_patients} tone="blue" />
            <StatCard label="Appointments" value={stats.total_appointments} tone="green" />
            <StatCard label="Pending Workload" value={stats.pending_appointments} tone="amber" />
            <StatCard label="Doctors" value={stats.total_doctors} tone="slate" />
          </div>
        )}

        {isAdmin && revenue && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <StatCard label="Net Revenue" value={`Rs. ${Number(revenue.net_revenue).toFixed(2)}`} tone="green" />
            <StatCard label="Refunded Amount" value={`Rs. ${Number(revenue.total_refunded_amount).toFixed(2)}`} tone="red" />
            <StatCard label="Pending Refund Requests" value={revenue.pending_refund_count} tone="amber" />
          </div>
        )}

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filteredReportCards.length === 0 ? (
            <EmptyState title="No reports in this category" description="Choose another category to view report modules." />
          ) : filteredReportCards.map((card) => {
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
                <div className="flex items-center justify-between gap-2">
                  <span>{card.title}</span>
                  <StatusBadge value={card.category} />
                </div>
              </Link>
            );
          })}
        </div>

        <SectionCard
          title="Export Center"
          subtitle="Authenticated CSV and JSON exports"
        >

          {visibleExportActions.length === 0 ? (
            <EmptyState title="No export actions available" description="Your current role does not have export permissions on this page." />
          ) : (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
              {visibleExportActions.map((action) => (
                <div key={action.id} className="rounded-lg border border-gray-200 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-900">{action.title}</h3>
                    <StatusBadge value={action.format} />
                  </div>
                  <p className="mb-3 text-xs text-gray-600">{action.description}</p>
                  <button
                    type="button"
                    onClick={() => runExport(action.id, action.run)}
                    disabled={activeExportId === action.id}
                    className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {activeExportId === action.id ? 'Exporting...' : 'Export'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {exportMessage && (
            <p className="mt-4 text-sm text-gray-700">{exportMessage}</p>
          )}

          {(isFinanceRole || isComplianceRole) && (
            <p className="mt-2 text-xs text-gray-500">
              Exports are role-protected and reflect your backend permissions.
            </p>
          )}
        </SectionCard>
      </div>
    </MainLayout>
  );
}
