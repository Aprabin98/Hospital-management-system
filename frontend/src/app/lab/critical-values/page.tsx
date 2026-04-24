'use client';

import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface CriticalValue {
  id: number;
  result: number;
  result_details: {
    id: number;
    booking_id: number;
    status: string;
    has_critical_values: boolean;
  };
  is_critical: boolean;
  urgency: 'IMMEDIATE' | 'URGENT' | 'PRIORITY';
  critical_fields: any[];
  notification_sent_at: string | null;
  notification_method: string;
  acknowledged_by_name: string | null;
  acknowledged_at: string | null;
  acknowledgment_notes: string;
  escalated_to_name: string | null;
  escalated_at: string | null;
  created_at: string;
  updated_at: string;
}

interface CriticalValuesResponse {
  count: number;
  results: CriticalValue[];
}

const URGENCY_COLORS: Record<string, string> = {
  IMMEDIATE: 'bg-red-100 text-red-800',
  URGENT: 'bg-orange-100 text-orange-800',
  PRIORITY: 'bg-yellow-100 text-yellow-800',
};

const URGENCY_ICONS: Record<string, string> = {
  IMMEDIATE: '🚨',
  URGENT: '⚠️',
  PRIORITY: '⏰',
};

export default function CriticalValuesPage() {
  const [criticalValues, setCriticalValues] = useState<CriticalValue[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedValue, setSelectedValue] = useState<CriticalValue | null>(null);
  const [acknowledgmentNotes, setAcknowledgmentNotes] = useState('');
  const [isAcknowledging, setIsAcknowledging] = useState(false);

  const { userRole } = useAuth();
  const role = (userRole || '').toUpperCase();
  const isDoctor = role === 'DOCTOR';

  useEffect(() => {
    const run = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<CriticalValuesResponse>('/lab/critical-values/pending/');
        setCriticalValues(response.results || []);
      } catch (error) {
        toast.error('Failed to load critical values');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };
    run();
  }, []);

  const handleAcknowledge = async () => {
    if (!selectedValue) return;

    try {
      setIsAcknowledging(true);
      const updated = await apiClient.patch<CriticalValue>(
        `/lab/critical-values/${selectedValue.id}/acknowledge/`,
        { notes: acknowledgmentNotes }
      );
      setCriticalValues(criticalValues.map(cv => cv.id === updated.id ? updated : cv));
      setSelectedValue(null);
      setAcknowledgmentNotes('');
      toast.success('Critical value acknowledged');
    } catch (error) {
      toast.error('Failed to acknowledge critical value');
      console.error(error);
    } finally {
      setIsAcknowledging(false);
    }
  };

  const pendingCount = criticalValues.filter(cv => !cv.acknowledged_at).length;
  const immediateCount = criticalValues.filter(cv => cv.urgency === 'IMMEDIATE' && !cv.acknowledged_at).length;

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.criticalLabValues}
      title="critical lab values"
      description="Critical lab values are restricted to clinical and laboratory escalation roles."
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Critical Lab Values</h1>
          <p className="mt-2 text-gray-600">Track critical values requiring immediate doctor acknowledgment</p>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-600">Total Critical Values</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{criticalValues.length}</p>
          </div>
          <div className="rounded-lg border border-orange-200 bg-orange-50 p-4 shadow-sm">
            <p className="text-sm text-orange-800">Pending Acknowledgments</p>
            <p className="mt-1 text-3xl font-bold text-orange-600">{pendingCount}</p>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
            <p className="text-sm text-red-800">Immediate Priority</p>
            <p className="mt-1 text-3xl font-bold text-red-600">{immediateCount}</p>
          </div>
        </div>

        {/* Critical Values List */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="space-y-2 p-4">
            {isLoading ? (
              <p className="text-center text-gray-500">Loading critical values...</p>
            ) : criticalValues.length === 0 ? (
              <p className="text-center text-gray-500">No critical values pending acknowledgment</p>
            ) : (
              criticalValues.map(cv => (
                <div
                  key={cv.id}
                  className={`rounded border p-4 ${
                    cv.acknowledged_at
                      ? 'border-gray-200 bg-gray-50'
                      : 'border-red-200 bg-red-50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{URGENCY_ICONS[cv.urgency]}</span>
                        <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${URGENCY_COLORS[cv.urgency]}`}>
                          {cv.urgency}
                        </span>
                        {cv.acknowledged_at && (
                          <span className="inline-block rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-800">
                            ✓ Acknowledged
                          </span>
                        )}
                      </div>

                      <div className="mt-3 grid gap-2 md:grid-cols-2">
                        <div>
                          <p className="text-xs font-medium text-gray-600">Created</p>
                          <p className="text-sm text-gray-900">{new Date(cv.created_at).toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-600">Notification Method</p>
                          <p className="text-sm text-gray-900">{cv.notification_method}</p>
                        </div>
                        {cv.acknowledged_at && (
                          <>
                            <div>
                              <p className="text-xs font-medium text-gray-600">Acknowledged By</p>
                              <p className="text-sm text-gray-900">{cv.acknowledged_by_name || 'N/A'}</p>
                            </div>
                            <div>
                              <p className="text-xs font-medium text-gray-600">Acknowledged At</p>
                              <p className="text-sm text-gray-900">{new Date(cv.acknowledged_at).toLocaleString()}</p>
                            </div>
                          </>
                        )}
                      </div>

                      {cv.acknowledgment_notes && (
                        <div className="mt-3">
                          <p className="text-xs font-medium text-gray-600">Doctor&apos;s Notes</p>
                          <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{cv.acknowledgment_notes}</p>
                        </div>
                      )}

                      <div className="mt-3">
                        <p className="text-xs font-medium text-gray-600">Critical Fields</p>
                        <p className="text-sm text-gray-700 font-mono">
                          {JSON.stringify(cv.critical_fields, null, 2)}
                        </p>
                      </div>
                    </div>

                    {!cv.acknowledged_at && isDoctor && (
                      <button
                        onClick={() => setSelectedValue(cv)}
                        className="ml-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700"
                      >
                        Acknowledge Now
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Acknowledgment Panel */}
        {selectedValue && !selectedValue.acknowledged_at && (
          <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Acknowledge Critical Value</h2>
            <p className="mt-1 text-sm text-gray-600">Urgency: {selectedValue.urgency}</p>

            <div className="mt-4 space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Your Response</label>
                <textarea
                  value={acknowledgmentNotes}
                  onChange={e => setAcknowledgmentNotes(e.target.value)}
                  className="w-full rounded border border-gray-300 px-3 py-2"
                  rows={3}
                  placeholder="Describe any actions taken or medical decision made in response to this critical value"
                />
              </div>

              <div className="flex gap-2">
                <button
                  onClick={handleAcknowledge}
                  disabled={isAcknowledging}
                  className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:bg-green-300"
                >
                  Confirm Acknowledgment
                </button>
                <button
                  onClick={() => {
                    setSelectedValue(null);
                    setAcknowledgmentNotes('');
                  }}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50"
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
