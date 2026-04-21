'use client';

import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface DashboardMetrics {
  dispenses: {
    pending: number;
    approved: number;
    dispensed_today: number;
  };
  alerts: {
    unresolved_alerts: number;
    expired_medications: number;
    near_expiry_medications: number;
    low_stock_items: number;
  };
  controlled_drugs: {
    total_controlled_items: number;
    dispensed_today: number;
  };
  inventory: {
    total_items: number;
    total_value: number;
  };
}

export default function PharmacyDashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const userRole = useMemo(() => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('userRole');
  }, []);

  const role = (userRole || '').toUpperCase();
  const canAccessPharmacy = ['ADMIN', 'PHARMACIST'].includes(role);

  useEffect(() => {
    if (!canAccessPharmacy) return;

    const loadMetrics = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<DashboardMetrics>('/pharmacy/dashboard/');
        setMetrics(response);
      } catch (error) {
        toast.error('Failed to load pharmacy metrics');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadMetrics();
  }, [canAccessPharmacy]);

  if (!canAccessPharmacy) {
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
          <h1 className="text-3xl font-bold text-gray-900">Pharmacy Dashboard</h1>
          <p className="mt-2 text-gray-600">Medication management, dispensing queue, and inventory overview</p>
        </div>

        {isLoading ? (
          <div className="text-center text-gray-500 py-8">Loading pharmacy metrics...</div>
        ) : metrics ? (
          <>
            {/* Dispensing Metrics */}
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 shadow-sm">
                <p className="text-sm text-blue-800 font-medium">Pending Dispenses</p>
                <p className="mt-2 text-4xl font-bold text-blue-600">{metrics.dispenses.pending}</p>
                <p className="mt-1 text-xs text-blue-700">Awaiting approval or selection</p>
              </div>
              <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 shadow-sm">
                <p className="text-sm text-yellow-800 font-medium">Approved Dispenses</p>
                <p className="mt-2 text-4xl font-bold text-yellow-600">{metrics.dispenses.approved}</p>
                <p className="mt-1 text-xs text-yellow-700">Ready to dispense</p>
              </div>
              <div className="rounded-lg border border-green-200 bg-green-50 p-4 shadow-sm">
                <p className="text-sm text-green-800 font-medium">Dispensed Today</p>
                <p className="mt-2 text-4xl font-bold text-green-600">{metrics.dispenses.dispensed_today}</p>
                <p className="mt-1 text-xs text-green-700">Already handed out</p>
              </div>
            </div>

            {/* Alert Metrics */}
            <div>
              <h2 className="mb-4 text-lg font-semibold text-gray-900">⚠️ Alerts & Issues</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
                  <p className="text-sm text-red-800 font-medium">🚨 Unresolved Alerts</p>
                  <p className="mt-2 text-3xl font-bold text-red-600">{metrics.alerts.unresolved_alerts}</p>
                </div>
                <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 shadow-sm">
                  <p className="text-sm text-orange-800 font-medium">❌ Expired Medications</p>
                  <p className="mt-2 text-3xl font-bold text-orange-600">{metrics.alerts.expired_medications}</p>
                </div>
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 shadow-sm">
                  <p className="text-sm text-amber-800 font-medium">⏰ Near Expiry (3mo)</p>
                  <p className="mt-2 text-3xl font-bold text-amber-600">{metrics.alerts.near_expiry_medications}</p>
                </div>
                <div className="rounded-lg border border-purple-200 bg-purple-50 p-4 shadow-sm">
                  <p className="text-sm text-purple-800 font-medium">📦 Low Stock Items</p>
                  <p className="mt-2 text-3xl font-bold text-purple-600">{metrics.alerts.low_stock_items}</p>
                </div>
              </div>
            </div>

            {/* Controlled Drugs Metrics */}
            <div>
              <h2 className="mb-4 text-lg font-semibold text-gray-900">🔒 Controlled Drugs</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-4 shadow-sm">
                  <p className="text-sm text-indigo-800 font-medium">Total CII/IV/V Items</p>
                  <p className="mt-2 text-3xl font-bold text-indigo-600">{metrics.controlled_drugs.total_controlled_items}</p>
                </div>
                <div className="rounded-lg border border-pink-200 bg-pink-50 p-4 shadow-sm">
                  <p className="text-sm text-pink-800 font-medium">Dispensed Today</p>
                  <p className="mt-2 text-3xl font-bold text-pink-600">{metrics.controlled_drugs.dispensed_today}</p>
                </div>
              </div>
            </div>

            {/* Inventory Metrics */}
            <div>
              <h2 className="mb-4 text-lg font-semibold text-gray-900">📊 Inventory Status</h2>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                  <p className="text-sm text-gray-800 font-medium">Total Items in Stock</p>
                  <p className="mt-2 text-3xl font-bold text-gray-900">{metrics.inventory.total_items}</p>
                </div>
                <div className="rounded-lg border border-green-200 bg-green-50 p-4 shadow-sm">
                  <p className="text-sm text-green-800 font-medium">Total Inventory Value</p>
                  <p className="mt-2 text-3xl font-bold text-green-600">₹ {metrics.inventory.total_value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}</p>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="mb-4 text-lg font-semibold text-gray-900">Quick Actions</h2>
              <div className="grid gap-3 md:grid-cols-3">
                <a
                  href="/pharmacy/dispense"
                  className="inline-block rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                >
                  📋 Go to Dispense Queue
                </a>
                <a
                  href="/pharmacy/inventory"
                  className="inline-block rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
                >
                  📦 Manage Inventory
                </a>
                <a
                  href="/admin/pharmacy"
                  className="inline-block rounded-lg bg-gray-600 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-700"
                >
                  ⚙️ Pharmacy Settings
                </a>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center text-gray-500">Failed to load metrics</div>
        )}
      </div>
    </MainLayout>
  );
}
