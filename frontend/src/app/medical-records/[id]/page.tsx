'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

export default function MedicalRecordDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [record, setRecord] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get(`/medical-records/${id}/`);
        setRecord(response);
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
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm space-y-4">
            <div>
              <p className="text-sm text-gray-500">Patient</p>
              <p className="text-lg font-semibold text-gray-900">{record.patient || '-'}</p>
            </div>

            {fields.map(([label, value]) => (
              <div key={label}>
                <p className="text-sm text-gray-500">{label}</p>
                <p className="text-gray-800 whitespace-pre-line">{value || '-'}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
