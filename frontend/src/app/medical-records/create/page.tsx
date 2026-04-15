'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks';

interface PatientOption {
  id: number;
  full_name?: string;
  user?: {
    first_name?: string;
    last_name?: string;
    email?: string;
  };
}

export default function AddMedicalRecordPage() {
  const router = useRouter();
  const { userRole } = useAuth();

  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [patientId, setPatientId] = useState('');
  const [allergies, setAllergies] = useState('');
  const [chronicConditions, setChronicConditions] = useState('');
  const [surgicalHistory, setSurgicalHistory] = useState('');
  const [familyHistory, setFamilyHistory] = useState('');
  const [currentMedications, setCurrentMedications] = useState('');
  const [immunizationNotes, setImmunizationNotes] = useState('');
  const [emergencyNotes, setEmergencyNotes] = useState('');

  const [isLoadingPatients, setIsLoadingPatients] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const canCreateRecord = ['admin', 'doctor', 'receptionist'].includes((userRole || '').toLowerCase());

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setIsLoadingPatients(true);
      const response = await apiClient.get<{ results: PatientOption[] }>('/patients/?page_size=200');
      setPatients(response.results || []);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load patients');
    } finally {
      setIsLoadingPatients(false);
    }
  };

  const getPatientDisplayName = (patient: PatientOption) => {
    if (patient.full_name) return patient.full_name;
    const first = patient.user?.first_name || '';
    const last = patient.user?.last_name || '';
    const full = `${first} ${last}`.trim();
    return full || `Patient #${patient.id}`;
  };
  
      useEffect(() => {
        if (userRole && !canCreateRecord) {
          toast.error('Access denied. Redirecting to medical records.');
          router.replace('/medical-records');
        }
      }, [userRole, canCreateRecord, router]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!patientId) {
      toast.error('Please select a patient');
      return;
    }

    try {
      setIsSaving(true);

      await apiClient.post('/medical-records/create/', {
        patient: Number(patientId),
        allergies,
        chronic_conditions: chronicConditions,
        surgical_history: surgicalHistory,
        family_history: familyHistory,
        current_medications: currentMedications,
        immunization_notes: immunizationNotes,
        emergency_notes: emergencyNotes,
      });

      toast.success('Medical record created successfully');
      router.push('/medical-records');
    } catch (err: any) {
      const message = err?.message || 'Failed to create medical record';
      toast.error(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Link href="/medical-records" className="inline-block mb-2 font-medium text-blue-600 hover:text-blue-700">
            ← Back to Medical Records
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Add Record</h1>
          <p className="mt-2 text-gray-600">Create a complete medical record for a patient</p>
        </div>

        {!canCreateRecord && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 text-yellow-800">
            Your role does not have permission to create medical records.
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">Patient *</label>
            <select
              value={patientId}
              onChange={(e) => setPatientId(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              disabled={isLoadingPatients || isSaving || !canCreateRecord}
              required
            >
              <option value="">Select patient</option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {getPatientDisplayName(patient)}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Allergies</label>
              <textarea
                value={allergies}
                onChange={(e) => setAllergies(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Drug or food allergies"
                disabled={isSaving || !canCreateRecord}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Chronic Conditions</label>
              <textarea
                value={chronicConditions}
                onChange={(e) => setChronicConditions(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Diabetes, hypertension, etc."
                disabled={isSaving || !canCreateRecord}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Surgical History</label>
              <textarea
                value={surgicalHistory}
                onChange={(e) => setSurgicalHistory(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Past surgeries and dates"
                disabled={isSaving || !canCreateRecord}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Family History</label>
              <textarea
                value={familyHistory}
                onChange={(e) => setFamilyHistory(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Family medical background"
                disabled={isSaving || !canCreateRecord}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Current Medications</label>
              <textarea
                value={currentMedications}
                onChange={(e) => setCurrentMedications(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Current drugs and dosage"
                disabled={isSaving || !canCreateRecord}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Immunization Notes</label>
              <textarea
                value={immunizationNotes}
                onChange={(e) => setImmunizationNotes(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
                placeholder="Vaccination history"
                disabled={isSaving || !canCreateRecord}
              />
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-gray-700">Emergency Notes</label>
            <textarea
              value={emergencyNotes}
              onChange={(e) => setEmergencyNotes(e.target.value)}
              rows={4}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:ring-blue-500"
              placeholder="Emergency instructions and critical alerts"
              disabled={isSaving || !canCreateRecord}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={isSaving || !canCreateRecord}
              className="rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-gray-400"
            >
              {isSaving ? 'Saving...' : 'Create Record'}
            </button>
            <Link
              href="/medical-records"
              className="rounded-lg border border-gray-300 px-5 py-2 font-semibold text-gray-700 transition-colors hover:bg-gray-50"
            >
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </MainLayout>
  );
}
