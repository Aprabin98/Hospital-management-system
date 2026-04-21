'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';

interface Stay {
  id: number;
  patient_name: string;
  primary_diagnosis: string;
  status: 'ADMITTED' | 'DISCHARGED' | 'TRANSFERRED';
  bed_label: string;
  attending_doctor_name: string;
  expected_discharge_date: string | null;
  length_of_stay_days: number;
}

interface DashboardMetrics {
  stays: { active: number; discharged_today: number; transferred: number };
  rounds: { today: number };
  discharge: { pending_packages: number; finalized: number };
}

export default function IPDPage() {
  const [stays, setStays] = useState<Stay[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const userRole = useMemo(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('userRole');
  }, []);

  const role = (userRole || '').toUpperCase();
  const canAccess = ['ADMIN', 'DOCTOR', 'NURSE', 'RECEPTIONIST'].includes(role);

  useEffect(() => {
    if (!canAccess) return;

    const loadData = async () => {
      try {
        setIsLoading(true);
        const [stayResponse, dashboardResponse] = await Promise.all([
          apiClient.get<{ count: number; results: Stay[] }>('/ipd/stays/?active=true'),
          apiClient.get<DashboardMetrics>('/ipd/dashboard/'),
        ]);
        setStays(stayResponse.results || []);
        setMetrics(dashboardResponse);
      } catch (error) {
        toast.error('Failed to load inpatient data');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [canAccess]);

  if (!canAccess) {
    return (
      <MainLayout>
        <div className="p-6 text-center">
          <p className="font-semibold text-red-600">Access Denied. IPD roles required.</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <PageHeader
          title="Inpatient (IPD) Workflow"
          description="Admission to discharge management with rounds and discharge package."
          actions={
            <Link href="/ipd/doctor-rounds" className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">
              Doctor Rounds
            </Link>
          }
        />

        {metrics && (
          <div className="grid gap-4 md:grid-cols-3">
            <StatCard label="Active Admissions" value={metrics.stays.active} tone="blue" />
            <StatCard label="Rounds Today" value={metrics.rounds.today} tone="amber" />
            <StatCard label="Pending Discharge Packages" value={metrics.discharge.pending_packages} tone="green" />
          </div>
        )}

        <SectionCard title="Active IPD Patients" subtitle="Track admissions, progress, and discharge workflow from one board.">

          {isLoading ? (
            <div className="p-6 text-center text-gray-500">Loading active stays...</div>
          ) : stays.length === 0 ? (
            <EmptyState title="No active inpatient stays" description="Admissions will appear here once patients are moved into IPD." />
          ) : (
            <div className="divide-y divide-gray-100">
              {stays.map((stay) => (
                <div key={stay.id} className="flex flex-wrap items-center justify-between gap-4 px-4 py-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-base font-semibold text-gray-900">{stay.patient_name}</p>
                      <StatusBadge value={stay.status} />
                    </div>
                    <p className="text-sm text-gray-600">{stay.primary_diagnosis}</p>
                    <p className="text-xs text-gray-500">
                      {stay.bed_label || 'No bed assigned'} | {stay.attending_doctor_name || 'No attending doctor'} | LOS: {stay.length_of_stay_days} day(s)
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Link href={`/ipd/stays/${stay.id}`} className="rounded-md bg-slate-700 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800">
                      Open Stay
                    </Link>
                    <Link href={`/ipd/stays/${stay.id}/discharge`} className="rounded-md bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700">
                      Discharge
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </MainLayout>
  );
}
