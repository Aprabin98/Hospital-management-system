'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface AllergyItem {
  id: number;
  allergen: string;
  reaction: string;
  severity: string;
  status: string;
  notes: string;
  diagnosed_on: string | null;
  updated_at: string;
}

interface VitalLogItem {
  id: number;
  blood_pressure: string;
  pulse: number | null;
  temperature_c: number | null;
  respiratory_rate: number | null;
  oxygen_saturation: number | null;
  notes: string;
  recorded_at: string;
}

export default function MedicalRecordDetailPage() {
  const params = useParams<{ id?: string | string[] }>();
  const id = typeof params?.id === 'string' ? params.id : '';
  const [record, setRecord] = useState<any>(null);
  const [patientProfile, setPatientProfile] = useState<any>(null);
  const [allergies, setAllergies] = useState<AllergyItem[]>([]);
  const [vitals, setVitals] = useState<VitalLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get(`/medical-records/${id}/`);
        setRecord(response);

        if (response?.patient) {
          const patientId = typeof response.patient === 'object' ? response.patient.id : response.patient;
          const [patientRes, allergiesRes, vitalsRes] = await Promise.all([
            apiClient.get(`/patients/${patientId}/`),
            apiClient.get<{ count: number; results: AllergyItem[] }>(`/patients/${patientId}/allergies/`),
            apiClient.get<{ count: number; results: VitalLogItem[] }>(`/vital-logs/?patient=${patientId}&page_size=5`),
          ]);
          setPatientProfile(patientRes);
          setAllergies(allergiesRes.results || []);
          setVitals(vitalsRes.results || []);
        }
      } catch (err: any) {
        toast.error(err?.message || 'Failed to load medical record');
      } finally {
        setIsLoading(false);
      }
    };
    if (id) load();
  }, [id]);

  const fields = [
    ['Allergies', record?.allergies],
    ['Chronic Conditions', record?.chronic_conditions],
    ['Surgical History', record?.surgical_history],
    ['Family History', record?.family_history],
    ['Current Medications', record?.current_medications],
    ['Immunization Notes', record?.immunization_notes],
    ['Emergency Notes', record?.emergency_notes],
  ];

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Link href="/medical-records" className="text-blue-600 hover:text-blue-700 font-medium">← Back to Medical Records</Link>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">Medical Record Details</h1>
        </div>

        {isLoading && <p className="text-gray-600">Loading record...</p>}

        {!isLoading && !record && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">Medical record not found.</div>
        )}

        {record && (
          <div className="space-y-4">
            <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
              <div>
                <p className="text-sm text-gray-500">Patient</p>
                <p className="text-lg font-semibold text-gray-900">{patientProfile?.full_name || record.patient || '-'}</p>
                {patientProfile?.user?.email && <p className="text-sm text-gray-500">{patientProfile.user.email}</p>}
              </div>

              {fields.map(([label, value]) => (
                <div key={label}>
                  <p className="text-sm text-gray-500">{label}</p>
                  <p className="text-gray-800 whitespace-pre-line">{value || '-'}</p>
                </div>
              ))}
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-amber-900">Allergy Safety</h2>
                {allergies.length === 0 ? (
                  <p className="mt-2 text-sm text-amber-800">No recorded allergies.</p>
                ) : (
                  <div className="mt-3 space-y-2">
                    {allergies.map((allergy) => (
                      <div key={allergy.id} className="rounded-lg border border-amber-200 bg-white px-3 py-2 text-sm text-amber-900">
                        <p className="font-semibold">{allergy.allergen}</p>
                        <p>{allergy.reaction || 'Reaction not specified'} • {allergy.severity}</p>
                        <p className="text-xs text-amber-700">Status: {allergy.status}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-blue-900">Recent Vital Logs</h2>
                {vitals.length === 0 ? (
                  <p className="mt-2 text-sm text-blue-800">No recent vitals recorded.</p>
                ) : (
                  <div className="mt-3 space-y-2">
                    {vitals.map((vital) => (
                      <div key={vital.id} className="rounded-lg border border-blue-200 bg-white px-3 py-2 text-sm text-blue-900">
                        <p className="font-semibold">{new Date(vital.recorded_at).toLocaleString()}</p>
                        <p>BP {vital.blood_pressure || 'N/A'} | Pulse {vital.pulse ?? 'N/A'} | Temp {vital.temperature_c ?? 'N/A'} C</p>
                        <p>RR {vital.respiratory_rate ?? 'N/A'} | SpO2 {vital.oxygen_saturation ?? 'N/A'}</p>
                        {vital.notes && <p className="text-xs text-blue-700">{vital.notes}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
