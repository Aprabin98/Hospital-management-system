'use client';

import React, { useEffect, useState } from 'react';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface TriageItem {
  id: number;
  symptoms: string;
  priority: 'P1' | 'P2' | 'P3' | 'P4';
  priority_score: number;
  ai_summary: string;
  recommended_action: string;
  created_at: string;
}

export default function AITriagePage() {
  const [symptoms, setSymptoms] = useState('');
  const [durationDays, setDurationDays] = useState(1);
  const [painLevel, setPainLevel] = useState(0);
  const [flags, setFlags] = useState({
    has_fever: false,
    has_breathing_issue: false,
    has_chest_pain: false,
    has_heavy_bleeding: false,
    had_fainting_episode: false,
  });
  const [history, setHistory] = useState<TriageItem[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const fetchHistory = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<{ results: TriageItem[] }>('/ai-triage/');
      setHistory(response.results || []);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load triage history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const submitTriage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (symptoms.trim().length < 10) {
      toast.error('Please provide symptom details (at least 10 characters).');
      return;
    }

    try {
      setIsSaving(true);
      await apiClient.post('/ai-triage/', {
        symptoms,
        duration_days: durationDays,
        pain_level: painLevel,
        ...flags,
      });
      toast.success('Triage assessment completed successfully');
      setSymptoms('');
      setDurationDays(1);
      setPainLevel(0);
      setFlags({
        has_fever: false,
        has_breathing_issue: false,
        has_chest_pain: false,
        has_heavy_bleeding: false,
        had_fainting_episode: false,
      });
      fetchHistory();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to submit triage assessment');
    } finally {
      setIsSaving(false);
    }
  };

  const priorityStyle = (priority: TriageItem['priority']) => {
    if (priority === 'P1') return 'bg-red-100 text-red-800';
    if (priority === 'P2') return 'bg-orange-100 text-orange-800';
    if (priority === 'P3') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Triage</h1>
          <p className="text-gray-600">Describe symptoms to receive automated triage priority and recommendations.</p>
        </div>

        <form onSubmit={submitTriage} className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Symptoms</label>
            <textarea
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              rows={4}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              placeholder="Describe your symptoms in detail..."
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700">Duration (days)</label>
              <input
                type="number"
                min={1}
                value={durationDays}
                onChange={(e) => setDurationDays(Number(e.target.value) || 1)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Pain Level (0-10)</label>
              <input
                type="number"
                min={0}
                max={10}
                value={painLevel}
                onChange={(e) => setPainLevel(Number(e.target.value) || 0)}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
            {[
              ['has_fever', 'Fever'],
              ['has_breathing_issue', 'Breathing issue'],
              ['has_chest_pain', 'Chest pain'],
              ['has_heavy_bleeding', 'Heavy bleeding'],
              ['had_fainting_episode', 'Fainting episode'],
            ].map(([key, label]) => (
              <label key={key} className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={Boolean(flags[key as keyof typeof flags])}
                  onChange={(e) => setFlags((prev) => ({ ...prev, [key]: e.target.checked }))}
                />
                {label}
              </label>
            ))}
          </div>

          <button
            type="submit"
            disabled={isSaving}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isSaving ? 'Analyzing...' : 'Run Triage'}
          </button>
        </form>

        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Recent Triage History</h2>
          {isLoading ? (
            <p className="mt-3 text-sm text-gray-600">Loading history...</p>
          ) : history.length === 0 ? (
            <p className="mt-3 text-sm text-gray-600">No triage assessments yet.</p>
          ) : (
            <div className="mt-4 space-y-3">
              {history.map((item) => (
                <div key={item.id} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${priorityStyle(item.priority)}`}>
                      {item.priority}
                    </span>
                    <span className="text-xs text-gray-500">Score: {item.priority_score}</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-700">{item.ai_summary}</p>
                  <p className="mt-2 text-sm font-medium text-gray-900">{item.recommended_action}</p>
                  <p className="mt-2 text-xs text-gray-500">{new Date(item.created_at).toLocaleString()}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
