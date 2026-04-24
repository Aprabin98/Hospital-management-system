'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface Medicine {
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions: string;
}

interface Prescription {
  id: number;
  doctor_name: string;
  appointment_date: string;
  refill_status: string;
  notes: string;
  advice: string;
  items: Medicine[];
  pdf_file?: string;
  follow_up_date?: string;
}

export default function PrescriptionsPage() {
  const router = useRouter();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeOnly, setActiveOnly] = useState(true);
  const [userRole, setUserRole] = useState('');
  const [previewPrescriptionId, setPreviewPrescriptionId] = useState<number | null>(null);
  const [previewPdfUrl, setPreviewPdfUrl] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [editingPrescription, setEditingPrescription] = useState<any | null>(null);
  const [editingMedicines, setEditingMedicines] = useState<Medicine[]>([]);
  const [isSavingEdit, setIsSavingEdit] = useState(false);
  const isDoctor = userRole === 'DOCTOR';

  useEffect(() => {
    setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
  }, []);

  useEffect(() => {
    return () => {
      if (previewPdfUrl) {
        window.URL.revokeObjectURL(previewPdfUrl);
      }
    };
  }, [previewPdfUrl]);

  const fetchPrescriptions = useCallback(async () => {
    try {
      setIsLoading(true);
      const endpoint = activeOnly ? '/prescriptions/active/' : '/prescriptions/';
      const response = await apiClient.get(endpoint);
      setPrescriptions(Array.isArray(response) ? response : response.results || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load prescriptions');
      toast.error('Failed to load prescriptions');
    } finally {
      setIsLoading(false);
    }
  }, [activeOnly]);

  useEffect(() => {
    void fetchPrescriptions();
  }, [fetchPrescriptions]);

  const handleEditPrescription = (prescription: Prescription) => {
    setEditingPrescription(prescription);
    setEditingMedicines(prescription.items || []);
  };

  const handleAddMedicine = () => {
    setEditingMedicines([...editingMedicines, { 
      medicine_name: '', 
      dosage: '', 
      frequency: '', 
      duration: '', 
      instructions: '' 
    }]);
  };

  const handleRemoveMedicine = (index: number) => {
    setEditingMedicines(editingMedicines.filter((_, i) => i !== index));
  };

  const handleMedicineChange = (index: number, field: keyof Medicine, value: string) => {
    const newMedicines = [...editingMedicines];
    newMedicines[index] = { ...newMedicines[index], [field]: value };
    setEditingMedicines(newMedicines);
  };

  const handleSaveEdit = async () => {
    if (!editingPrescription) return;

    try {
      setIsSavingEdit(true);
      await apiClient.put(`/prescriptions/${editingPrescription.id}/update/`, {
        items: editingMedicines,
        notes: editingPrescription.notes,
        advice: editingPrescription.advice,
      });
      
      toast.success('Prescription updated successfully');
      setEditingPrescription(null);
      fetchPrescriptions();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to update prescription');
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleDownloadPrescription = async (prescriptionId: number) => {
    try {
      const token = localStorage.getItem('authToken');
      const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/prescriptions/${prescriptionId}/download-pdf/`, {
        method: 'GET',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        let message = 'Download failed';
        try {
          const payload = await response.json();
          message = payload?.detail || payload?.message || message;
        } catch {
          // Non-JSON error response; keep default message.
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `prescription_${prescriptionId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to download prescription');
    }
  };

  const closePdfPreview = () => {
    if (previewPdfUrl) {
      window.URL.revokeObjectURL(previewPdfUrl);
    }
    setPreviewPdfUrl(null);
    setPreviewPrescriptionId(null);
    setIsPreviewLoading(false);
  };

  const handleViewPrescriptionPdf = async (prescriptionId: number) => {
    try {
      setIsPreviewLoading(true);
      setPreviewPrescriptionId(prescriptionId);

      const token = localStorage.getItem('authToken');
      const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
      const response = await fetch(`${baseUrl}/prescriptions/${prescriptionId}/download-pdf/`, {
        method: 'GET',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        let message = 'Unable to load PDF preview';
        try {
          const payload = await response.json();
          message = payload?.detail || payload?.message || message;
        } catch {
          // Non-JSON error response; keep default message.
        }
        throw new Error(message);
      }

      const blob = await response.blob();
      const nextUrl = window.URL.createObjectURL(blob);

      if (previewPdfUrl) {
        window.URL.revokeObjectURL(previewPdfUrl);
      }

      setPreviewPdfUrl(nextUrl);
    } catch (err: any) {
      closePdfPreview();
      toast.error(err?.message || 'Failed to load prescription PDF preview');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Prescriptions</h1>
            <p className="mt-2 text-gray-600">Manage your prescriptions and medications</p>
          </div>
          {isDoctor && (
          <div>
            <Link
              href="/appointments"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Write From Completed Appointment
            </Link>
          </div>
          )}
        </div>

        {/* Filter */}
        <div className="flex items-center justify-between gap-4 rounded-lg border border-gray-200 bg-white px-4 py-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-600">Show active prescriptions only</span>
          </label>
          <span className="text-xs font-medium text-gray-500">
            {activeOnly ? 'Showing: ACTIVE + REFILLS_AVAILABLE' : 'Showing: All prescriptions'}
          </span>
        </div>

        {!isLoading && (
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              {activeOnly ? 'Active Prescriptions' : 'All Prescriptions'}
            </h2>
            <span className="text-sm text-gray-600">{prescriptions.length} found</span>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-lg text-gray-600">Loading...</div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {!isLoading && prescriptions.length === 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
            <p className="text-gray-600">
              {activeOnly
                ? 'No active prescriptions found (ACTIVE or REFILLS_AVAILABLE).'
                : 'No prescriptions found.'}
            </p>
          </div>
        )}

        {!isLoading && prescriptions.length > 0 && (
          <div className="space-y-4">
            {prescriptions.map((prescription: Prescription) => (
              <div key={prescription.id} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Dr. {prescription.doctor_name}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      Appointment: {prescription.appointment_date}
                    </p>
                  </div>
                  <span className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${
                    prescription.refill_status === 'ACTIVE' || prescription.refill_status === 'REFILLS_AVAILABLE'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {prescription.refill_status}
                  </span>
                </div>

                {/* Notes */}
                {prescription.notes && (
                  <div className="mb-4 p-3 bg-gray-50 rounded">
                    <p className="text-sm font-medium text-gray-700">Notes:</p>
                    <p className="text-sm text-gray-600 mt-1">{prescription.notes}</p>
                  </div>
                )}

                {/* Advice */}
                {prescription.advice && (
                  <div className="mb-4 p-3 bg-blue-50 rounded">
                    <p className="text-sm font-medium text-blue-700">Doctor&apos;s Advice:</p>
                    <p className="text-sm text-blue-600 mt-1">{prescription.advice}</p>
                  </div>
                )}

                {/* Medicines */}
                {prescription.items && prescription.items.length > 0 && (
                  <div className="mb-4">
                    <p className="text-sm font-medium text-gray-700 mb-2">Medicines:</p>
                    <ul className="space-y-2 text-sm">
                      {prescription.items.map((item: any, idx: number) => (
                        <li key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div>
                            <p className="font-medium text-gray-900">{item.medicine_name}</p>
                            <p className="text-xs text-gray-600">
                              {item.dosage} • {item.frequency} • {item.duration}
                            </p>
                            {item.instructions && (
                              <p className="text-xs text-gray-500 mt-1">{item.instructions}</p>
                            )}
                          </div>
                          <span className="text-xs text-gray-500">{item.timing}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Meta Info */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                  <div className="text-sm text-gray-600">
                    Follow-up: {prescription.follow_up_date || 'Not scheduled'}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleViewPrescriptionPdf(prescription.id)}
                      className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                    >
                      View
                    </button>
                    {isDoctor && (
                      <button
                        onClick={() => handleEditPrescription(prescription)}
                        className="text-sm text-orange-600 hover:text-orange-700 font-medium"
                      >
                        Edit
                      </button>
                    )}
                    <button
                      onClick={() => handleDownloadPrescription(prescription.id)}
                      className="text-sm text-green-600 hover:text-green-700 font-medium"
                    >
                      Download
                    </button>
                    {prescription.refill_status === 'REFILLS_AVAILABLE' && (
                      <button className="text-sm text-purple-600 hover:text-purple-700 font-medium">
                        Refill
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* PDF Preview Modal */}
      {previewPrescriptionId && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-5xl w-full h-[85vh] flex flex-col">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">Prescription PDF Preview #{previewPrescriptionId}</h2>
              <button
                onClick={closePdfPreview}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 p-4">
              {isPreviewLoading && (
                <div className="h-full flex items-center justify-center text-gray-600">Loading PDF preview...</div>
              )}
              {!isPreviewLoading && previewPdfUrl && (
                <iframe
                  title="Prescription PDF Preview"
                  src={previewPdfUrl}
                  className="w-full h-full border border-gray-200 rounded"
                />
              )}
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => handleDownloadPrescription(previewPrescriptionId)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Download PDF
              </button>
              <button
                onClick={closePdfPreview}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingPrescription && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
            <div className="p-6 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">Edit Prescription</h2>
              <button
                onClick={() => setEditingPrescription(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              {editingMedicines.map((medicine, index) => (
                <div key={index} className="border border-gray-200 rounded p-3">
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    <input
                      type="text"
                      value={medicine.medicine_name}
                      onChange={(e) => handleMedicineChange(index, 'medicine_name', e.target.value)}
                      placeholder="Medicine name"
                      className="text-sm border border-gray-300 rounded px-2 py-1 bg-white text-gray-900 placeholder:text-gray-500"
                    />
                    <input
                      type="text"
                      value={medicine.dosage}
                      onChange={(e) => handleMedicineChange(index, 'dosage', e.target.value)}
                      placeholder="Dosage"
                      className="text-sm border border-gray-300 rounded px-2 py-1 bg-white text-gray-900 placeholder:text-gray-500"
                    />
                    <input
                      type="text"
                      value={medicine.frequency}
                      onChange={(e) => handleMedicineChange(index, 'frequency', e.target.value)}
                      placeholder="Frequency"
                      className="text-sm border border-gray-300 rounded px-2 py-1 bg-white text-gray-900 placeholder:text-gray-500"
                    />
                    <input
                      type="text"
                      value={medicine.duration}
                      onChange={(e) => handleMedicineChange(index, 'duration', e.target.value)}
                      placeholder="Duration"
                      className="text-sm border border-gray-300 rounded px-2 py-1 bg-white text-gray-900 placeholder:text-gray-500"
                    />
                  </div>
                  <input
                    type="text"
                    value={medicine.instructions}
                    onChange={(e) => handleMedicineChange(index, 'instructions', e.target.value)}
                    placeholder="Instructions"
                    className="w-full text-sm border border-gray-300 rounded px-2 py-1 mb-2 bg-white text-gray-900 placeholder:text-gray-500"
                  />
                  {editingMedicines.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveMedicine(index)}
                      className="text-xs text-red-600 hover:text-red-700"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={editingPrescription.notes || ''}
                  onChange={(e) => setEditingPrescription({ ...editingPrescription, notes: e.target.value })}
                  rows={3}
                  className="w-full text-sm border border-gray-300 rounded px-3 py-2 bg-white text-gray-900 placeholder:text-gray-500"
                  placeholder="Additional notes"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doctor Advice</label>
                <textarea
                  value={editingPrescription.advice || ''}
                  onChange={(e) => setEditingPrescription({ ...editingPrescription, advice: e.target.value })}
                  rows={3}
                  className="w-full text-sm border border-gray-300 rounded px-3 py-2 bg-white text-gray-900 placeholder:text-gray-500"
                  placeholder="Follow-up advice"
                />
              </div>

              <button
                type="button"
                onClick={handleAddMedicine}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                + Add Medicine
              </button>
            </div>

            <div className="p-6 border-t border-gray-200 flex justify-end gap-2">
              <button
                onClick={() => setEditingPrescription(null)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveEdit}
                disabled={isSavingEdit}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {isSavingEdit ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
