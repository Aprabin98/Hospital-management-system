'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useRoleAccess } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface DischargePackage {
  id: number;
  discharge_summary: string;
  discharge_diagnoses: string;
  discharge_instructions: string;
  follow_up_date: string;
  follow_up_provider: string;
  follow_up_specialty: string;
  nursing_clearance: boolean;
  pharmacy_clearance: boolean;
  billing_clearance: boolean;
  final_approved: boolean;
  checklist_complete: boolean;
}

export default function DischargePage() {
  const params = useParams<{ stayId: string }>();
  const stayId = params?.stayId;

  const [form, setForm] = useState({
    discharge_summary: '',
    discharge_diagnoses: '',
    discharge_instructions: '',
    follow_up_date: '',
    follow_up_provider: '',
    follow_up_specialty: '',
    nursing_clearance: false,
    pharmacy_clearance: false,
    billing_clearance: false,
  });
  const [current, setCurrent] = useState<DischargePackage | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const { canAccess } = useRoleAccess(ACCESS_MATRIX.ipdRounds);

  const loadCurrent = useCallback(async () => {
    if (!stayId) return;
    try {
      const pkg = await apiClient.get<DischargePackage>(`/ipd/stays/${stayId}/discharge/`);
      setCurrent(pkg);
      setForm({
        discharge_summary: pkg.discharge_summary || '',
        discharge_diagnoses: pkg.discharge_diagnoses || '',
        discharge_instructions: pkg.discharge_instructions || '',
        follow_up_date: pkg.follow_up_date || '',
        follow_up_provider: pkg.follow_up_provider || '',
        follow_up_specialty: pkg.follow_up_specialty || '',
        nursing_clearance: !!pkg.nursing_clearance,
        pharmacy_clearance: !!pkg.pharmacy_clearance,
        billing_clearance: !!pkg.billing_clearance,
      });
    } catch {
      setCurrent(null);
    }
  }, [stayId]);

  useEffect(() => {
    if (!canAccess) return;
    void loadCurrent();
  }, [canAccess, loadCurrent]);

  const savePackage = async (finalize = false) => {
    if (!stayId) return;

    if (!form.discharge_summary.trim() || !form.discharge_instructions.trim() || !form.follow_up_date) {
      toast.error('Summary, instructions and follow-up date are required.');
      return;
    }

    try {
      setIsSaving(true);
      const payload = {
        ...form,
        doctor_signoff: true,
        finalize,
      };
      const response = await apiClient.post<DischargePackage>(`/ipd/stays/${stayId}/discharge/`, payload);
      setCurrent(response);
      toast.success(finalize ? 'Discharge finalized successfully' : 'Discharge package saved');
    } catch (error) {
      toast.error('Failed to save discharge package');
      console.error(error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.ipdRounds}
      title="discharge package"
      description="Discharge package access is restricted to physician and administrator roles."
    >
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Discharge Package - Stay #{stayId}</h1>
          <p className="text-sm text-gray-600">Complete all mandatory fields and clearances before final approval.</p>
        </div>

        <div className="space-y-4 rounded-lg border border-gray-200 bg-white p-5">
          <textarea
            value={form.discharge_summary}
            onChange={(e) => setForm((prev) => ({ ...prev, discharge_summary: e.target.value }))}
            rows={4}
            className="w-full rounded-md border border-gray-300 px-3 py-2"
            placeholder="Discharge summary"
          />

          <textarea
            value={form.discharge_diagnoses}
            onChange={(e) => setForm((prev) => ({ ...prev, discharge_diagnoses: e.target.value }))}
            rows={3}
            className="w-full rounded-md border border-gray-300 px-3 py-2"
            placeholder="Discharge diagnoses"
          />

          <textarea
            value={form.discharge_instructions}
            onChange={(e) => setForm((prev) => ({ ...prev, discharge_instructions: e.target.value }))}
            rows={4}
            className="w-full rounded-md border border-gray-300 px-3 py-2"
            placeholder="Discharge instructions"
          />

          <div className="grid gap-3 md:grid-cols-3">
            <input
              type="date"
              value={form.follow_up_date}
              onChange={(e) => setForm((prev) => ({ ...prev, follow_up_date: e.target.value }))}
              className="rounded-md border border-gray-300 px-3 py-2"
            />
            <input
              type="text"
              value={form.follow_up_provider}
              onChange={(e) => setForm((prev) => ({ ...prev, follow_up_provider: e.target.value }))}
              placeholder="Follow-up provider"
              className="rounded-md border border-gray-300 px-3 py-2"
            />
            <input
              type="text"
              value={form.follow_up_specialty}
              onChange={(e) => setForm((prev) => ({ ...prev, follow_up_specialty: e.target.value }))}
              placeholder="Follow-up specialty"
              className="rounded-md border border-gray-300 px-3 py-2"
            />
          </div>

          <div className="grid gap-2 md:grid-cols-3">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.nursing_clearance}
                onChange={(e) => setForm((prev) => ({ ...prev, nursing_clearance: e.target.checked }))}
              />
              Nursing clearance
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.pharmacy_clearance}
                onChange={(e) => setForm((prev) => ({ ...prev, pharmacy_clearance: e.target.checked }))}
              />
              Pharmacy clearance
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={form.billing_clearance}
                onChange={(e) => setForm((prev) => ({ ...prev, billing_clearance: e.target.checked }))}
              />
              Billing clearance
            </label>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => savePackage(false)}
              disabled={isSaving}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
            >
              Save Package
            </button>
            <button
              onClick={() => savePackage(true)}
              disabled={isSaving}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
            >
              Finalize Discharge
            </button>
          </div>
        </div>

        {current && (
          <div className="rounded-lg border border-gray-200 bg-slate-50 p-4 text-sm">
            <p>Checklist complete: <strong>{current.checklist_complete ? 'Yes' : 'No'}</strong></p>
            <p>Final approved: <strong>{current.final_approved ? 'Yes' : 'No'}</strong></p>
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}
