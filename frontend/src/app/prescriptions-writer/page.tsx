'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';
import { useRouter, useSearchParams } from 'next/navigation';

interface Patient {
  id: number;
  user: { first_name: string; last_name: string };
  blood_group?: string;
  phone?: string;
}

interface AppointmentContext {
  id: number;
  patient: number;
  patient_name?: string;
}

interface Medicine {
  name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions: string;
}

function PrescriptionsWriterPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const appointmentId = searchParams.get('appointmentId');
  const patientIdFromQuery = searchParams.get('patientId');

  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [selectedPatientId, setSelectedPatientId] = useState<number | null>(null);
  const [medicines, setMedicines] = useState<Medicine[]>([
    { name: '', dosage: '', frequency: '', duration: '', instructions: '' }
  ]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isPrefillingPatient, setIsPrefillingPatient] = useState(false);

  useEffect(() => {
    const timer = setTimeout(async () => {
      const term = searchTerm.trim();
      if (term.length < 1) {
        setPatients([]);
        return;
      }

      try {
        setIsLoadingSuggestions(true);
        const response = await apiClient.get<{ results?: Patient[] }>(`/patients/?q=${encodeURIComponent(term)}&page_size=8`);
        setPatients(response.results || []);
      } catch {
        setPatients([]);
      } finally {
        setIsLoadingSuggestions(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    if (!appointmentId) {
      return;
    }

    const id = Number(appointmentId);
    if (Number.isNaN(id)) {
      return;
    }

    const run = async () => {
      try {
        setIsPrefillingPatient(true);
        const appointment = await apiClient.get<AppointmentContext>(`/appointments/${id}/`);
        const patientId = Number(appointment.patient);
        if (Number.isNaN(patientId)) {
          return;
        }

        setSelectedPatientId(patientId);

        try {
          const patientResponse = await apiClient.get<Patient>(`/patients/${patientId}/`);
          setSelectedPatient(patientResponse);
          setSearchTerm(`${patientResponse.user?.first_name || ''} ${patientResponse.user?.last_name || ''}`.trim());
          return;
        } catch {
          // Fallback to appointment patient_name when patient detail is unavailable.
          const fullName = (appointment.patient_name || '').trim();
          setSelectedPatient({
            id: patientId,
            user: {
              first_name: fullName || `Patient ${patientId}`,
              last_name: '',
            },
          });
          setSearchTerm(fullName || `Patient ${patientId}`);
        }
      } catch {
        // Keep manual selection flow when appointment prefill fails.
      } finally {
        setIsPrefillingPatient(false);
      }
    };

    run();
  }, [appointmentId]);

  useEffect(() => {
    if (!patientIdFromQuery || selectedPatientId) {
      return;
    }

    const id = Number(patientIdFromQuery);
    if (Number.isNaN(id)) {
      return;
    }

    const run = async () => {
      try {
        setIsPrefillingPatient(true);
        const response = await apiClient.get<Patient>(`/patients/${id}/`);
        setSelectedPatient(response);
        setSelectedPatientId(response.id);
        setSearchTerm(`${response.user?.first_name || ''} ${response.user?.last_name || ''}`.trim());
      } catch {
        // Keep manual selection flow when direct patient prefill fails.
      } finally {
        setIsPrefillingPatient(false);
      }
    };

    run();
  }, [patientIdFromQuery, selectedPatientId]);

  const handleAddMedicine = () => {
    setMedicines([...medicines, { name: '', dosage: '', frequency: '', duration: '', instructions: '' }]);
  };

  const handleRemoveMedicine = (index: number) => {
    setMedicines(medicines.filter((_, i) => i !== index));
  };

  const handleMedicineChange = (index: number, field: keyof Medicine, value: string) => {
    const newMedicines = [...medicines];
    newMedicines[index] = { ...newMedicines[index], [field]: value };
    setMedicines(newMedicines);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!appointmentId) {
      toast.error('Appointment is required. Start from a completed appointment.');
      return;
    }

    if (!selectedPatientId) {
      toast.error('Please select a patient');
      return;
    }

    if (medicines.some(m => !m.name || !m.dosage || !m.frequency)) {
      toast.error('Please fill all medicine details');
      return;
    }

    try {
      setIsSaving(true);
      const prescriptionData = {
        appointment: Number(appointmentId),
        patient: selectedPatientId,
        medicines: medicines.map(m => ({
          medicine_name: m.name,
          dosage: m.dosage,
          frequency: m.frequency,
          duration: m.duration,
          instructions: m.instructions,
        })),
      };

      await apiClient.post('/prescriptions/create/', prescriptionData);
      toast.success('Prescription created successfully');
      
      // Reset form
      setSelectedPatient(null);
      setSelectedPatientId(null);
      setMedicines([{ name: '', dosage: '', frequency: '', duration: '', instructions: '' }]);
      router.push('/prescriptions');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to create prescription');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <MainLayout>
      <div className="max-w-4xl">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Write Prescription</h1>
          <p className="mt-2 text-gray-600">Create a prescription for a completed appointment</p>
          {appointmentId && (
            <p className="mt-1 text-sm text-indigo-700 font-medium">Appointment ID: {appointmentId}</p>
          )}
          {!appointmentId && (
            <p className="mt-1 text-sm text-red-600 font-medium">No appointment selected. Open this from a completed appointment.</p>
          )}
        </div>

        <form onSubmit={handleSubmit} className="mt-6 rounded-lg border border-gray-200 bg-white shadow-sm">
          {/* Patient Selection */}
          <div className="border-b border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900">Select Patient</h2>
          </div>

          <div className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Search Patient</label>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setShowSuggestions(true);
                }}
                disabled={Boolean(appointmentId) || Boolean(patientIdFromQuery)}
                onFocus={() => setShowSuggestions(true)}
                placeholder="Search by name, phone number, email, or patient ID..."
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
              />
              {isPrefillingPatient && (
                <p className="mt-2 text-xs text-indigo-700">Loading patient from appointment...</p>
              )}
              <p className="mt-2 text-xs text-gray-600">
                Search tips: try patient name ("Rahul"), number ("98"), email, or ID ("12").
              </p>
            </div>

            {showSuggestions && searchTerm && (
              <div className="rounded-lg border border-gray-200 max-h-64 overflow-y-auto">
                {isLoadingSuggestions ? (
                  <div className="px-4 py-3 text-gray-600 text-center">Searching...</div>
                ) : patients.length > 0 ? (
                  patients.map((patient) => (
                    <button
                      key={patient.id}
                      type="button"
                      onClick={() => {
                        setSelectedPatient(patient);
                        setSelectedPatientId(patient.id);
                        setSearchTerm(`${patient.user.first_name} ${patient.user.last_name}`.trim());
                        setShowSuggestions(false);
                      }}
                      className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b last:border-b-0 transition-colors"
                    >
                      <p className="font-medium text-gray-900">
                        {patient.user.first_name} {patient.user.last_name}
                      </p>
                      <p className="text-sm text-gray-600">
                        ID: {patient.id} | Blood Group: {patient.blood_group || 'N/A'} | Phone: {patient.phone || 'N/A'}
                      </p>
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-3 text-gray-600 text-center">
                    No patients found. Try searching by name, number, or patient ID.
                  </div>
                )}
              </div>
            )}

            {selectedPatient && (
              <div className="rounded-lg bg-blue-50 border border-blue-200 p-4">
                <p className="text-sm font-medium text-gray-900">Selected Patient:</p>
                <p className="text-lg font-semibold text-blue-700 mt-1">
                  {selectedPatient.user.first_name} {selectedPatient.user.last_name}
                </p>
                <div className="mt-2 grid grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Blood Group:</span> {selectedPatient.blood_group || 'N/A'}
                  </div>
                  <div>
                    <span className="font-medium">Phone:</span> {selectedPatient.phone || 'N/A'}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Medicines Section */}
          {selectedPatient && (
            <>
              <div className="border-t border-gray-200 p-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900">Medicines</h2>
                  <button
                    type="button"
                    onClick={handleAddMedicine}
                    className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                  >
                    + Add Medicine
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-6">
                {medicines.map((medicine, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-4">
                    <div className="flex justify-between items-center">
                      <h3 className="font-medium text-gray-900">Medicine {index + 1}</h3>
                      {medicines.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveMedicine(index)}
                          className="text-red-600 hover:text-red-700 text-sm font-medium"
                        >
                          Remove
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Medicine Name *</label>
                        <input
                          type="text"
                          value={medicine.name}
                          onChange={(e) => handleMedicineChange(index, 'name', e.target.value)}
                          placeholder="e.g., Paracetamol"
                          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Dosage *</label>
                        <input
                          type="text"
                          value={medicine.dosage}
                          onChange={(e) => handleMedicineChange(index, 'dosage', e.target.value)}
                          placeholder="e.g., 500 mg"
                          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Frequency *</label>
                        <input
                          type="text"
                          value={medicine.frequency}
                          onChange={(e) => handleMedicineChange(index, 'frequency', e.target.value)}
                          placeholder="e.g., 2 times daily"
                          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700">Duration</label>
                        <input
                          type="text"
                          value={medicine.duration}
                          onChange={(e) => handleMedicineChange(index, 'duration', e.target.value)}
                          placeholder="e.g., 7 days"
                          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700">Instructions</label>
                      <textarea
                        value={medicine.instructions}
                        onChange={(e) => handleMedicineChange(index, 'instructions', e.target.value)}
                        placeholder="e.g., Take after meals, avoid dairy"
                        rows={2}
                        className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Submit Button */}
          <div className="border-t border-gray-200 p-6 flex gap-4">
            <button
              type="submit"
              disabled={isSaving || !selectedPatientId || !appointmentId}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium"
            >
              {isSaving ? 'Creating...' : 'Create Prescription'}
            </button>
            <button
              type="button"
              onClick={() => router.back()}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </MainLayout>
  );
}

export default function PrescriptionsWriterPage() {
  return (
    <Suspense
      fallback={
        <MainLayout>
          <div className="max-w-4xl">
            <div className="mt-6 rounded-lg border border-gray-200 bg-white p-6 text-gray-600 shadow-sm">
              Loading prescription writer...
            </div>
          </div>
        </MainLayout>
      }
    >
      <PrescriptionsWriterPageContent />
    </Suspense>
  );
}
