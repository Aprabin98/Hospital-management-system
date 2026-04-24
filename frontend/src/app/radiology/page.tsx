'use client';

import React, { FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';
import { EmptyState, PageHeader, SectionCard, StatCard, StatusBadge } from '@/components/UI';

interface ImagingCatalogItem {
  id: number;
  name: string;
  modality: string;
  price: string;
  turnaround_hours: number;
}

interface ImagingOrder {
  id: number;
  patient: number;
  patient_name: string;
  catalog_item: number;
  catalog_name: string;
  modality: string;
  priority: 'ROUTINE' | 'URGENT' | 'STAT';
  status: 'ORDERED' | 'SCHEDULED' | 'IN_PROGRESS' | 'REPORTED' | 'RELEASED' | 'CANCELLED';
  clinical_notes: string;
  created_at: string;
  report?: {
    is_critical?: boolean;
  };
}

interface PatientOption {
  id: number;
  full_name: string;
}

const initialForm = {
  patient: '',
  catalog_item: '',
  priority: 'ROUTINE' as 'ROUTINE' | 'URGENT' | 'STAT',
  clinical_notes: '',
};

export default function RadiologyDashboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [catalog, setCatalog] = useState<ImagingCatalogItem[]>([]);
  const [orders, setOrders] = useState<ImagingOrder[]>([]);
  const [patientQuery, setPatientQuery] = useState('');
  const [patientOptions, setPatientOptions] = useState<PatientOption[]>([]);
  const [form, setForm] = useState({ ...initialForm });

  const { userRole } = useAuth();
  const canAccess = useMemo(
    () => ACCESS_MATRIX.radiology.includes((userRole || '').toUpperCase() as (typeof ACCESS_MATRIX.radiology)[number]),
    [userRole]
  );

  const summary = useMemo(
    () => ({
      active: orders.filter((order) => ['ORDERED', 'SCHEDULED', 'IN_PROGRESS'].includes(order.status)).length,
      pendingReports: orders.filter((order) => ['IN_PROGRESS', 'REPORTED'].includes(order.status)).length,
      criticalFlags: orders.filter((order) => Boolean(order.report?.is_critical)).length,
    }),
    [orders]
  );

  const loadRadiologyData = async () => {
    try {
      setIsLoading(true);
      const [catalogData, orderData] = await Promise.all([
        apiClient.get<ImagingCatalogItem[]>('/radiology/catalog/'),
        apiClient.get<ImagingOrder[]>('/radiology/orders/'),
      ]);

      const sortedOrders = [...(orderData || [])].sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      setCatalog(catalogData || []);
      setOrders(sortedOrders);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to load radiology data');
    } finally {
      setIsLoading(false);
    }
  };

  const searchPatients = async (query: string) => {
    if (!query.trim()) {
      setPatientOptions([]);
      return;
    }

    try {
      const data = await apiClient.get<{ results: PatientOption[] }>(`/patients/?q=${encodeURIComponent(query)}&page_size=8`);
      setPatientOptions(data.results || []);
    } catch {
      setPatientOptions([]);
    }
  };

  useEffect(() => {
    if (!canAccess) return;
    loadRadiologyData();
  }, [canAccess]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      searchPatients(patientQuery);
    }, 250);
    return () => clearTimeout(timeout);
  }, [patientQuery]);

  const submitOrder = async (e: FormEvent) => {
    e.preventDefault();

    if (!form.patient || !form.catalog_item) {
      toast.error('Patient and imaging study are required');
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.post('/radiology/orders/', {
        patient: Number(form.patient),
        catalog_item: Number(form.catalog_item),
        priority: form.priority,
        clinical_notes: form.clinical_notes.trim(),
      });
      toast.success('Imaging order created');
      setForm({ ...initialForm });
      setPatientQuery('');
      setPatientOptions([]);
      await loadRadiologyData();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to create imaging order');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.radiology}
      title="radiology dashboard"
      description="Radiology workflow is limited to approved ordering and imaging operations roles."
    >
      <div className="space-y-6">
        <PageHeader
          title="Radiology Dashboard"
          description="Create imaging orders, monitor worklist, and release reports."
          actions={
            <Link
              href="/radiology/history"
              className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            >
              Open Imaging History
            </Link>
          }
        />

        <div className="grid gap-4 md:grid-cols-3">
          <StatCard label="Active Studies" value={summary.active} tone="amber" />
          <StatCard label="Reports In Queue" value={summary.pendingReports} tone="blue" />
          <StatCard label="Critical Findings" value={summary.criticalFlags} tone="red" />
        </div>

        <SectionCard title="Order Imaging Study" subtitle="Book a patient imaging study from the active catalog.">
          <form className="grid gap-4 md:grid-cols-2" onSubmit={submitOrder}>
            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">Search patient</label>
              <input
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={patientQuery}
                onChange={(e) => {
                  setPatientQuery(e.target.value);
                  setForm((prev) => ({ ...prev, patient: '' }));
                }}
                placeholder="Type patient name"
              />
              {patientOptions.length > 0 && (
                <div className="mt-2 max-h-40 overflow-auto rounded-lg border border-gray-200 bg-white">
                  {patientOptions.map((patient) => (
                    <button
                      type="button"
                      key={patient.id}
                      className="block w-full border-b border-gray-100 px-3 py-2 text-left text-sm hover:bg-gray-50"
                      onClick={() => {
                        setForm((prev) => ({ ...prev, patient: String(patient.id) }));
                        setPatientQuery(patient.full_name);
                        setPatientOptions([]);
                      }}
                    >
                      {patient.full_name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Imaging study</label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={form.catalog_item}
                onChange={(e) => setForm((prev) => ({ ...prev, catalog_item: e.target.value }))}
              >
                <option value="">Select study</option>
                {catalog.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name} ({item.modality})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Priority</label>
              <select
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                value={form.priority}
                onChange={(e) => setForm((prev) => ({ ...prev, priority: e.target.value as typeof prev.priority }))}
              >
                <option value="ROUTINE">Routine</option>
                <option value="URGENT">Urgent</option>
                <option value="STAT">Stat</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="mb-1 block text-sm font-medium text-gray-700">Clinical notes</label>
              <textarea
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                rows={3}
                value={form.clinical_notes}
                onChange={(e) => setForm((prev) => ({ ...prev, clinical_notes: e.target.value }))}
                placeholder="Reason for imaging request"
              />
            </div>

            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={isSaving}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {isSaving ? 'Creating...' : 'Create Imaging Order'}
              </button>
            </div>
          </form>
        </SectionCard>

        <SectionCard title="Radiology Worklist" subtitle="Track active imaging studies and jump into reporting.">
          {isLoading ? (
            <div className="p-6 text-center text-gray-500">Loading radiology worklist...</div>
          ) : orders.length === 0 ? (
            <EmptyState title="No imaging orders" description="New imaging orders will appear here." />
          ) : (
            <div className="divide-y divide-gray-100">
              {orders.map((order) => (
                <div key={order.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-gray-900">IMG-{order.id} {order.patient_name}</p>
                      <StatusBadge value={order.status} />
                      <StatusBadge value={order.priority} />
                    </div>
                    <p className="text-sm text-gray-600">
                      {order.catalog_name} ({order.modality})
                    </p>
                    {order.clinical_notes ? <p className="text-xs text-gray-500">{order.clinical_notes}</p> : null}
                  </div>
                  <Link
                    href={`/radiology/studies/${order.id}`}
                    className="rounded-md bg-slate-700 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-800"
                  >
                    Open Study
                  </Link>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      </div>
    </ProtectedPage>
  );
}
