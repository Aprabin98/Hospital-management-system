'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface Stay {
  id: number;
  patient_name: string;
  primary_diagnosis: string;
  length_of_stay_days: number;
  bed_label: string;
}

export default function DoctorRoundsPage() {
  const [stays, setStays] = useState<Stay[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const { userRole } = useAuth();
  const canAccess = useMemo(
    () => ACCESS_MATRIX.ipdRounds.includes((userRole || '').toUpperCase() as (typeof ACCESS_MATRIX.ipdRounds)[number]),
    [userRole]
  );

  useEffect(() => {
    if (!canAccess) return;

    const load = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<{ count: number; results: Stay[] }>('/ipd/stays/?active=true');
        setStays(response.results || []);
      } catch (error) {
        toast.error('Failed to load doctor rounds list');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    load();
  }, [canAccess]);

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.ipdRounds}
      title="doctor rounds"
      description="Doctor rounds are restricted to physicians and administrators."
    >
      <div className="space-y-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Doctor IPD Rounds</h1>
          <p className="text-sm text-gray-600">Open a stay to add today&apos;s round and progress notes.</p>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4">
          {isLoading ? (
            <div className="py-6 text-center text-gray-500">Loading...</div>
          ) : stays.length === 0 ? (
            <div className="py-6 text-center text-gray-500">No active stays assigned.</div>
          ) : (
            <div className="space-y-3">
              {stays.map((stay) => (
                <div key={stay.id} className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-gray-200 p-3">
                  <div>
                    <p className="font-semibold text-gray-900">{stay.patient_name}</p>
                    <p className="text-sm text-gray-600">{stay.primary_diagnosis}</p>
                    <p className="text-xs text-gray-500">{stay.bed_label || 'No bed assigned'} | LOS: {stay.length_of_stay_days} day(s)</p>
                  </div>
                  <Link href={`/ipd/stays/${stay.id}`} className="rounded-md bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700">
                    Open Stay
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </ProtectedPage>
  );
}
