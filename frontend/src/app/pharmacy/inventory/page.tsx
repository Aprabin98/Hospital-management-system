'use client';

import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface MedicationInventory {
  id: number;
  medication_name: string;
  batch_number: string;
  lot_number: string;
  quantity: number;
  unit: string;
  unit_cost: number;
  total_value: number;
  expiry_date: string;
  days_to_expiry: number;
  is_expired: boolean;
  is_near_expiry: boolean;
  is_blocked: boolean;
  is_controlled_drug: boolean;
  manufacturer: string;
  received_by_name: string;
}

interface InventoryResponse {
  count: number;
  results: MedicationInventory[];
}

export default function InventoryManagementPage() {
  const [inventory, setInventory] = useState<MedicationInventory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filterExpired, setFilterExpired] = useState('all');
  const [filterControlled, setFilterControlled] = useState('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [formData, setFormData] = useState({
    medication_name: '',
    batch_number: '',
    lot_number: '',
    manufacturer: '',
    quantity: '',
    unit: 'TABLET',
    unit_cost: '',
    manufacture_date: '',
    expiry_date: '',
    is_controlled_drug: false,
  });

  const userRole = useMemo(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('userRole');
  }, []);

  const role = (userRole || '').toUpperCase();
  const canManageInventory = ['ADMIN', 'PHARMACIST'].includes(role);

  useEffect(() => {
    if (!canManageInventory) return;

    const loadInventory = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<InventoryResponse>('/pharmacy/medications/');
        setInventory(response.results || []);
      } catch (error) {
        toast.error('Failed to load inventory');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadInventory();
  }, [canManageInventory]);

  const handleAddMedication = async () => {
    if (!formData.medication_name || !formData.batch_number || !formData.quantity) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      const payload = {
        ...formData,
        quantity: parseInt(formData.quantity),
        unit_cost: parseFloat(formData.unit_cost),
      };

      const newMed = await apiClient.post('/pharmacy/medications/', payload);
      setInventory([newMed, ...inventory]);
      setShowAddForm(false);
      setFormData({
        medication_name: '',
        batch_number: '',
        lot_number: '',
        manufacturer: '',
        quantity: '',
        unit: 'TABLET',
        unit_cost: '',
        manufacture_date: '',
        expiry_date: '',
        is_controlled_drug: false,
      });
      toast.success('Medication added to inventory');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to add medication');
      console.error(error);
    }
  };

  const handleUpdateQuantity = async (medId: number, newQty: number) => {
    try {
      const updated = await apiClient.patch(`/pharmacy/medications/${medId}/`, {
        quantity: newQty,
      });

      setInventory(inventory.map(m => m.id === medId ? updated : m));
      toast.success('Quantity updated');
    } catch (error) {
      toast.error('Failed to update quantity');
      console.error(error);
    }
  };

  const filteredInventory = inventory.filter(med => {
    if (filterExpired === 'expired' && !med.is_expired) return false;
    if (filterExpired === 'near_expiry' && !med.is_near_expiry) return false;
    if (filterExpired === 'valid' && (med.is_expired || med.is_near_expiry)) return false;

    if (filterControlled === 'controlled' && !med.is_controlled_drug) return false;
    if (filterControlled === 'non_controlled' && med.is_controlled_drug) return false;

    return true;
  });

  const stats = {
    total: inventory.length,
    expired: inventory.filter(m => m.is_expired).length,
    near_expiry: inventory.filter(m => m.is_near_expiry).length,
    low_stock: inventory.filter(m => m.quantity < 5 && !m.is_expired).length,
    controlled: inventory.filter(m => m.is_controlled_drug).length,
    total_value: inventory.reduce((sum, m) => sum + m.total_value, 0),
  };

  if (!canManageInventory) {
    return (
      <MainLayout>
        <div className="p-6 text-center">
          <p className="text-red-600 font-semibold">Access Denied. Pharmacist role required.</p>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Medication Inventory</h1>
          <p className="mt-2 text-gray-600">Track stock levels, expiry dates, and batch management</p>
        </div>

        {/* KPI Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-600">Total Items</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{stats.total}</p>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
            <p className="text-sm text-red-800">❌ Expired</p>
            <p className="mt-1 text-3xl font-bold text-red-600">{stats.expired}</p>
          </div>
          <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 shadow-sm">
            <p className="text-sm text-orange-800">⏰ Near Expiry</p>
            <p className="mt-1 text-3xl font-bold text-orange-600">{stats.near_expiry}</p>
          </div>
          <div className="rounded-lg border border-green-200 bg-green-50 p-4 shadow-sm">
            <p className="text-sm text-green-800">Total Value</p>
            <p className="mt-1 text-3xl font-bold text-green-600">₹{(stats.total_value / 100000).toFixed(1)}L</p>
          </div>
        </div>

        {/* Filters */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Filters</h3>
          <div className="grid gap-3 md:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <select
                value={filterExpired}
                onChange={e => setFilterExpired(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All</option>
                <option value="valid">Valid (Not Expired)</option>
                <option value="near_expiry">Near Expiry (3mo)</option>
                <option value="expired">Expired</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
              <select
                value={filterControlled}
                onChange={e => setFilterControlled(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="all">All</option>
                <option value="non_controlled">Non-Controlled</option>
                <option value="controlled">Controlled (CII/IV/V)</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
              >
                + Add Medication
              </button>
            </div>
          </div>
        </div>

        {/* Add Medication Form */}
        {showAddForm && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">Add New Medication</h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Medication Name *</label>
                <input
                  type="text"
                  value={formData.medication_name}
                  onChange={e => setFormData({ ...formData, medication_name: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  placeholder="e.g. Paracetamol 500mg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Batch Number *</label>
                <input
                  type="text"
                  value={formData.batch_number}
                  onChange={e => setFormData({ ...formData, batch_number: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  placeholder="e.g. BTH20240115"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Lot Number</label>
                <input
                  type="text"
                  value={formData.lot_number}
                  onChange={e => setFormData({ ...formData, lot_number: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Manufacturer *</label>
                <input
                  type="text"
                  value={formData.manufacturer}
                  onChange={e => setFormData({ ...formData, manufacturer: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity *</label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={e => setFormData({ ...formData, quantity: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                <select
                  value={formData.unit}
                  onChange={e => setFormData({ ...formData, unit: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                >
                  <option value="TABLET">Tablet</option>
                  <option value="CAPSULE">Capsule</option>
                  <option value="ML">ML</option>
                  <option value="VIAL">Vial</option>
                  <option value="STRIP">Strip</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Unit Cost (₹) *</label>
                <input
                  type="number"
                  value={formData.unit_cost}
                  onChange={e => setFormData({ ...formData, unit_cost: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  step="0.01"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Manufacture Date</label>
                <input
                  type="date"
                  value={formData.manufacture_date}
                  onChange={e => setFormData({ ...formData, manufacture_date: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date *</label>
                <input
                  type="date"
                  value={formData.expiry_date}
                  onChange={e => setFormData({ ...formData, expiry_date: e.target.value })}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                />
              </div>
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_controlled_drug}
                    onChange={e => setFormData({ ...formData, is_controlled_drug: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm font-medium text-gray-700">🔒 Controlled Drug (CII/IV/V)</span>
                </label>
              </div>
            </div>
            <div className="mt-4 flex gap-2">
              <button
                onClick={handleAddMedication}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
              >
                Add Medication
              </button>
              <button
                onClick={() => setShowAddForm(false)}
                className="rounded-lg bg-gray-300 px-4 py-2 text-sm font-semibold text-gray-800 hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Inventory List */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="space-y-2 p-4">
            {isLoading ? (
              <p className="text-center text-gray-500">Loading inventory...</p>
            ) : filteredInventory.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No medications match the selected filters</p>
            ) : (
              filteredInventory.map(med => (
                <div key={med.id} className="rounded border border-gray-200 p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{med.medication_name}</h3>
                      <p className="text-xs text-gray-600">
                        Batch: {med.batch_number} | Lot: {med.lot_number || 'N/A'} | Manufacturer: {med.manufacturer}
                      </p>

                      {/* Status Badges */}
                      <div className="mt-2 flex flex-wrap gap-1">
                        {med.is_expired && (
                          <span className="inline-block rounded bg-red-100 px-2 py-1 text-xs font-semibold text-red-800">
                            ❌ EXPIRED
                          </span>
                        )}
                        {med.is_near_expiry && !med.is_expired && (
                          <span className="inline-block rounded bg-orange-100 px-2 py-1 text-xs font-semibold text-orange-800">
                            ⏰ NEAR EXPIRY ({med.days_to_expiry} days)
                          </span>
                        )}
                        {med.is_blocked && (
                          <span className="inline-block rounded bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-800">
                            🚫 BLOCKED
                          </span>
                        )}
                        {med.is_controlled_drug && (
                          <span className="inline-block rounded bg-indigo-100 px-2 py-1 text-xs font-semibold text-indigo-800">
                            🔒 CONTROLLED
                          </span>
                        )}
                        {med.quantity < 5 && !med.is_expired && (
                          <span className="inline-block rounded bg-yellow-100 px-2 py-1 text-xs font-semibold text-yellow-800">
                            📉 LOW STOCK
                          </span>
                        )}
                      </div>

                      {/* Stock & Value */}
                      <div className="mt-2 grid gap-2 md:grid-cols-4">
                        <div>
                          <p className="text-xs font-medium text-gray-600">Stock</p>
                          <p className="text-sm font-semibold text-gray-900">
                            {med.quantity} {med.unit}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-600">Unit Cost</p>
                          <p className="text-sm font-semibold text-gray-900">₹{med.unit_cost.toFixed(2)}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-600">Total Value</p>
                          <p className="text-sm font-semibold text-green-600">₹{med.total_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-600">Expiry Date</p>
                          <p className="text-sm font-semibold text-gray-900">{med.expiry_date}</p>
                        </div>
                      </div>
                    </div>

                    {/* Update Button */}
                    <div className="ml-4">
                      <input
                        type="number"
                        defaultValue={med.quantity}
                        onBlur={e => {
                          const newQty = parseInt(e.target.value);
                          if (newQty !== med.quantity) {
                            handleUpdateQuantity(med.id, newQty);
                          }
                        }}
                        className="w-20 rounded border border-gray-300 px-2 py-1 text-sm"
                        min="0"
                      />
                      <p className="mt-1 text-xs text-gray-600">Edit qty</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
