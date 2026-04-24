'use client';

import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface Medication {
  id: number;
  medication_name: string;
  batch_number: string;
  expiry_date: string;
  quantity_available: number;
}

interface DispensingTransaction {
  id: number;
  prescription_details: {
    id: number;
    medicine_name: string;
    dosage: string;
    frequency: string;
    duration: string;
  };
  patient_name: string;
  medication_details: Medication | null;
  quantity_dispensed: number;
  status: 'PENDING' | 'APPROVED' | 'DISPENSED' | 'REFUSED' | 'RETURNED';
  is_substituted: boolean;
  substitution_reason?: string;
  contraindication_notes?: string;
}

interface PendingQueueResponse {
  count: number;
  results: DispensingTransaction[];
}

export default function PendingDispenseQueuePage() {
  const [queue, setQueue] = useState<DispensingTransaction[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTransaction, setSelectedTransaction] = useState<DispensingTransaction | null>(null);
  const [showDispenseForm, setShowDispenseForm] = useState(false);

  const [dispenseFormData, setDispenseFormData] = useState({
    medication_id: '',
    quantity_dispensed: '',
    is_substituted: false,
    substitution_reason: '',
    contraindication_checked: false,
    contraindication_notes: '',
  });

  const { userRole } = useAuth();
  const role = (userRole || '').toUpperCase();
  const canDispense = ACCESS_MATRIX.pharmacy.includes(role as (typeof ACCESS_MATRIX.pharmacy)[number]);

  useEffect(() => {
    if (!canDispense) return;

    const loadData = async () => {
      try {
        setIsLoading(true);
        const [queueRes, medRes] = await Promise.all([
          apiClient.get<PendingQueueResponse>('/pharmacy/pending-dispense/'),
          apiClient.get<{ count: number; results: Medication[] }>('/pharmacy/medications/'),
        ]);

        setQueue(queueRes.results || []);
        setMedications(medRes.results || []);
      } catch (error) {
        toast.error('Failed to load pending dispenses');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [canDispense]);

  const handleStartDispense = (transaction: DispensingTransaction) => {
    setSelectedTransaction(transaction);
    setShowDispenseForm(true);
    setDispenseFormData({
      medication_id: '',
      quantity_dispensed: '',
      is_substituted: false,
      substitution_reason: '',
      contraindication_checked: false,
      contraindication_notes: '',
    });
  };

  const handleDispenseSubmit = async () => {
    if (!selectedTransaction || !dispenseFormData.medication_id || !dispenseFormData.quantity_dispensed) {
      toast.error('Please fill in all required fields');
      return;
    }

    try {
      const payload = {
        prescription_id: selectedTransaction.prescription_details.id,
        inventory_id: parseInt(dispenseFormData.medication_id),
        quantity_dispensed: parseInt(dispenseFormData.quantity_dispensed),
        is_substituted: dispenseFormData.is_substituted,
        substitution_reason: dispenseFormData.substitution_reason || null,
        contraindication_checked: dispenseFormData.contraindication_checked,
        contraindication_notes: dispenseFormData.contraindication_notes || null,
      };

      await apiClient.post('/pharmacy/dispense-transaction/', payload);

      setQueue(queue.filter(t => t.id !== selectedTransaction.id));
      setShowDispenseForm(false);
      setSelectedTransaction(null);
      toast.success('Dispense transaction created');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create dispense transaction');
      console.error(error);
    }
  };

  const handleApproveDispense = async (transaction: DispensingTransaction) => {
    try {
      await apiClient.patch(`/pharmacy/dispense-transaction/${transaction.id}/`, {
        status: 'APPROVED',
      });

      setQueue(queue.map(t => t.id === transaction.id ? { ...t, status: 'APPROVED' } : t));
      toast.success('Dispense approved');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to approve dispense');
      console.error(error);
    }
  };

  const handleCompleteDispense = async (transaction: DispensingTransaction) => {
    try {
      await apiClient.patch(`/pharmacy/dispense-transaction/${transaction.id}/`, {
        status: 'DISPENSED',
      });

      setQueue(queue.filter(t => t.id !== transaction.id));
      toast.success('Medication dispensed');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to complete dispense');
      console.error(error);
    }
  };

  const pendingCount = queue.filter(t => t.status === 'PENDING').length;
  const approvedCount = queue.filter(t => t.status === 'APPROVED').length;

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.pharmacy}
      title="dispense queue"
      description="Medication dispensing is restricted to pharmacy-authorized roles."
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Pending Dispense Queue</h1>
          <p className="mt-2 text-gray-600">Prescriptions awaiting medication selection and dispensing</p>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
            <p className="text-sm text-blue-800">Total Pending</p>
            <p className="mt-1 text-3xl font-bold text-blue-600">{queue.length}</p>
          </div>
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 shadow-sm">
            <p className="text-sm text-yellow-800">Awaiting Selection</p>
            <p className="mt-1 text-3xl font-bold text-yellow-600">{pendingCount}</p>
          </div>
          <div className="rounded-lg border border-green-200 bg-green-50 p-4 shadow-sm">
            <p className="text-sm text-green-800">Approved & Ready</p>
            <p className="mt-1 text-3xl font-bold text-green-600">{approvedCount}</p>
          </div>
        </div>

        {/* Pending Queue List */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="space-y-2 p-4">
            {isLoading ? (
              <p className="text-center text-gray-500">Loading pending dispenses...</p>
            ) : queue.length === 0 ? (
              <p className="text-center text-gray-500 py-8">✅ No pending dispenses. All caught up!</p>
            ) : (
              queue.map(transaction => (
                <div key={transaction.id} className="rounded border border-gray-200 p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Patient & Prescription Info */}
                      <div className="mb-2">
                        <h3 className="font-medium text-gray-900">👤 {transaction.patient_name}</h3>
                        <p className="text-xs text-gray-600">
                          💊 {transaction.prescription_details.medicine_name} - {transaction.prescription_details.dosage}
                        </p>
                        <p className="text-xs text-gray-600">
                          📋 {transaction.prescription_details.frequency} for {transaction.prescription_details.duration}
                        </p>
                      </div>

                      {/* Status Badge */}
                      <div className="mb-3">
                        <span
                          className={`inline-block rounded-full px-2 py-1 text-xs font-semibold ${
                            transaction.status === 'PENDING'
                              ? 'bg-blue-100 text-blue-800'
                              : transaction.status === 'APPROVED'
                              ? 'bg-green-100 text-green-800'
                              : transaction.status === 'DISPENSED'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {transaction.status}
                        </span>
                        {transaction.is_substituted && (
                          <span className="ml-2 inline-block rounded-full bg-orange-100 px-2 py-1 text-xs font-semibold text-orange-800">
                            🔄 Substituted
                          </span>
                        )}
                      </div>

                      {/* Current Medication (if selected) */}
                      {transaction.medication_details && (
                        <div className="mb-3 rounded bg-gray-50 p-2">
                          <p className="text-xs font-medium text-gray-700">✓ Medication Selected:</p>
                          <p className="text-sm text-gray-900">{transaction.medication_details.medication_name}</p>
                          <p className="text-xs text-gray-600">
                            Batch: {transaction.medication_details.batch_number} | Exp: {transaction.medication_details.expiry_date}
                          </p>
                          <p className="text-xs text-gray-600">Available: {transaction.medication_details.quantity_available} units</p>
                          <p className="text-xs text-gray-600">To Dispense: {transaction.quantity_dispensed} units</p>
                        </div>
                      )}

                      {/* Contraindication Notes */}
                      {transaction.contraindication_notes && (
                        <div className="mb-3 rounded bg-yellow-50 p-2 border border-yellow-200">
                          <p className="text-xs font-medium text-yellow-800">⚠️ Contraindication Notes:</p>
                          <p className="text-xs text-yellow-700">{transaction.contraindication_notes}</p>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="ml-4 space-y-2">
                      {transaction.status === 'PENDING' && !transaction.medication_details && (
                        <button
                          onClick={() => handleStartDispense(transaction)}
                          className="block whitespace-nowrap rounded bg-indigo-600 px-3 py-1 text-xs font-semibold text-white hover:bg-indigo-700"
                        >
                          Select Medication
                        </button>
                      )}
                      {transaction.status === 'PENDING' && transaction.medication_details && (
                        <button
                          onClick={() => handleApproveDispense(transaction)}
                          className="block whitespace-nowrap rounded bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-700"
                        >
                          Approve
                        </button>
                      )}
                      {transaction.status === 'APPROVED' && (
                        <button
                          onClick={() => handleCompleteDispense(transaction)}
                          className="block whitespace-nowrap rounded bg-purple-600 px-3 py-1 text-xs font-semibold text-white hover:bg-purple-700"
                        >
                          Mark Dispensed
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Dispense Form Modal */}
        {showDispenseForm && selectedTransaction && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              Select Medication for {selectedTransaction.patient_name}
            </h2>

            <div className="space-y-4">
              {/* Prescribed Medicine Info */}
              <div className="rounded bg-blue-50 p-3">
                <p className="text-xs font-medium text-blue-800">Prescribed Medicine</p>
                <p className="text-sm font-semibold text-gray-900">{selectedTransaction.prescription_details.medicine_name}</p>
                <p className="text-xs text-gray-600">{selectedTransaction.prescription_details.dosage}</p>
              </div>

              {/* Medication Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Select Available Medication *
                </label>
                <select
                  value={dispenseFormData.medication_id}
                  onChange={e => setDispenseFormData({ ...dispenseFormData, medication_id: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                >
                  <option value="">-- Choose Medication --</option>
                  {medications.map(med => (
                    <option key={med.id} value={med.id}>
                      {med.medication_name} (Batch: {med.batch_number}) - {med.quantity_available} units
                    </option>
                  ))}
                </select>
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity to Dispense *</label>
                <input
                  type="number"
                  value={dispenseFormData.quantity_dispensed}
                  onChange={e => setDispenseFormData({ ...dispenseFormData, quantity_dispensed: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  placeholder="e.g. 10"
                  min="1"
                />
              </div>

              {/* Substitution */}
              <div className="rounded bg-yellow-50 p-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={dispenseFormData.is_substituted}
                    onChange={e => setDispenseFormData({ ...dispenseFormData, is_substituted: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">🔄 Substituting with different medicine?</span>
                </label>
              </div>

              {dispenseFormData.is_substituted && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Substitution Reason</label>
                  <textarea
                    value={dispenseFormData.substitution_reason}
                    onChange={e => setDispenseFormData({ ...dispenseFormData, substitution_reason: e.target.value })}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    rows={2}
                    placeholder="Why are you substituting?"
                  />
                </div>
              )}

              {/* Contraindication Check */}
              <div className="rounded bg-orange-50 p-3">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={dispenseFormData.contraindication_checked}
                    onChange={e => setDispenseFormData({ ...dispenseFormData, contraindication_checked: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">⚠️ Checked for contraindications & allergies</span>
                </label>
              </div>

              {dispenseFormData.contraindication_checked && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Contraindication Notes (if any)</label>
                  <textarea
                    value={dispenseFormData.contraindication_notes}
                    onChange={e => setDispenseFormData({ ...dispenseFormData, contraindication_notes: e.target.value })}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    rows={2}
                    placeholder="Document any concerns or findings"
                  />
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2">
                <button
                  onClick={handleDispenseSubmit}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                >
                  Create Dispense Transaction
                </button>
                <button
                  onClick={() => setShowDispenseForm(false)}
                  className="rounded-lg bg-gray-300 px-4 py-2 text-sm font-semibold text-gray-800 hover:bg-gray-400"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}
