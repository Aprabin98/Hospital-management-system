'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface WaitingEntry {
  id: number;
  patient: string;
  doctor: string;
  date: string;
  priority: number;
  status: string;
}

interface NoShowPrediction {
  appointment_id: number;
  patient: string;
  doctor: string;
  date: string;
  probability: number;
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  status: string;
}

function getErrorMessage(err: unknown, fallback: string) {
  if (err && typeof err === 'object' && 'message' in err && typeof (err as { message?: unknown }).message === 'string') {
    return (err as { message: string }).message;
  }
  return fallback;
}

export default function QueueOpsPage() {
  const [loading, setLoading] = useState(true);
  const [waitingList, setWaitingList] = useState<WaitingEntry[]>([]);
  const [predictions, setPredictions] = useState<NoShowPrediction[]>([]);
  const [selectedWaitingId, setSelectedWaitingId] = useState<number | null>(null);
  const [priority, setPriority] = useState<'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [waitingResponse, predictionResponse] = await Promise.all([
        apiClient.get<{ count: number; results: WaitingEntry[] }>('/appointments/waiting-list/queue/'),
        apiClient.get<{ count: number; results: NoShowPrediction[] }>('/appointments/no-show/dashboard/'),
      ]);
      setWaitingList(waitingResponse.results || []);
      setPredictions(predictionResponse.results || []);
    } catch {
      toast.error('Failed to load queue operations data');
    } finally {
      setLoading(false);
    }
  };

  const highRisk = useMemo(() => predictions.filter((item) => item.risk_level === 'HIGH'), [predictions]);

  const promoteWaiting = async (id: number) => {
    try {
      await apiClient.post(`/appointments/waiting-list/${id}/promote/`, {});
      toast.success('Patient promoted from waiting list');
      loadData();
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Unable to promote patient'));
    }
  };

  const updatePriority = async () => {
    if (!selectedWaitingId) return;
    try {
      const priorityMap: Record<'HIGH' | 'MEDIUM' | 'LOW', number> = {
        HIGH: 90,
        MEDIUM: 60,
        LOW: 30,
      };

      await apiClient.post(`/appointments/waiting-list/${selectedWaitingId}/priority/`, {
        priority: priorityMap[priority],
      });
      toast.success('Waiting list priority updated');
      setSelectedWaitingId(null);
      loadData();
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Unable to update waiting list priority'));
    }
  };

  const updateNoShowOutcome = async (prediction: NoShowPrediction, outcome: 'showed' | 'no_show') => {
    try {
      await apiClient.post(`/appointments/no-show/${prediction.appointment_id}/outcome/`, {
        outcome,
      });
      toast.success(`No-show outcome set to ${outcome}`);
      loadData();
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Failed to update no-show outcome'));
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Waiting List and No-Show Operations</h1>
            <p className="mt-2 text-gray-600">Manage queue promotion, priority, and high-risk no-show outcomes in one place.</p>
          </div>
          <button onClick={loadData} className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Refresh</button>
        </div>

        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading queue workflows...</div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-xl font-semibold text-gray-900">Waiting List</h2>
              {waitingList.length === 0 ? (
                <div className="rounded bg-gray-50 p-4 text-sm text-gray-600">No patients currently in waiting list.</div>
              ) : (
                <div className="space-y-3">
                  {waitingList.map((entry) => (
                    <div key={entry.id} className="rounded border border-gray-200 p-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{entry.patient}</p>
                          <p className="text-sm text-gray-600">Doctor: {entry.doctor} | Priority: {entry.priority}</p>
                          <p className="text-sm text-gray-500">Date: {entry.date}</p>
                        </div>
                        <div className="flex gap-2">
                          <button onClick={() => promoteWaiting(entry.id)} className="rounded bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-700">Promote</button>
                          <button onClick={() => { setSelectedWaitingId(entry.id); setPriority('HIGH'); }} className="rounded border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 hover:bg-amber-100">Priority</button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h2 className="mb-4 text-xl font-semibold text-gray-900">No-Show Prediction Desk</h2>
              <div className="mb-4 rounded bg-red-50 p-3 text-sm text-red-700">High-risk appointments: {highRisk.length}</div>
              {predictions.length === 0 ? (
                <div className="rounded bg-gray-50 p-4 text-sm text-gray-600">No prediction data found.</div>
              ) : (
                <div className="space-y-3">
                  {predictions.map((item) => (
                    <div key={item.appointment_id} className="rounded border border-gray-200 p-3">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="font-medium text-gray-900">{item.patient}</p>
                          <p className="text-sm text-gray-600">Doctor: {item.doctor}</p>
                          <p className="text-sm text-gray-500">{item.date}</p>
                        </div>
                        <span className={`rounded-full px-2 py-1 text-xs font-semibold ${item.risk_level === 'HIGH' ? 'bg-red-100 text-red-700' : item.risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-700' : 'bg-green-100 text-green-700'}`}>
                          {item.risk_level} ({Math.round(item.probability * 100)}%)
                        </span>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        <button onClick={() => updateNoShowOutcome(item, 'showed')} className="rounded border border-green-300 bg-green-50 px-2 py-1 text-xs font-medium text-green-700 hover:bg-green-100">Mark Showed</button>
                        <button onClick={() => updateNoShowOutcome(item, 'no_show')} className="rounded border border-red-300 bg-red-50 px-2 py-1 text-xs font-medium text-red-700 hover:bg-red-100">Mark No-Show</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        {selectedWaitingId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
              <h3 className="mb-3 text-lg font-semibold text-gray-900">Set Waiting Priority</h3>
              <select value={priority} onChange={(e) => setPriority(e.target.value as 'HIGH' | 'MEDIUM' | 'LOW')} className="w-full rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900">
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
              <div className="mt-4 flex gap-3">
                <button onClick={() => setSelectedWaitingId(null)} className="flex-1 rounded border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                <button onClick={updatePriority} className="flex-1 rounded bg-amber-600 px-3 py-2 text-sm font-medium text-white hover:bg-amber-700">Update</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
