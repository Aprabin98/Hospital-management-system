'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface AnalysisItem {
  id: number;
  saved?: boolean;
  title: string;
  report_type: string;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' | string;
  ai_summary?: string;
  recommendations?: string;
  created_at: string;
}

export default function ReportReaderPage() {
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);

  const fetchAnalyses = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<{ results: AnalysisItem[] }>('/ai-report-reader/');
      setAnalyses(response.results || []);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load report analyses');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) {
      toast.error('Please select a report file');
      return;
    }

    const formData = new FormData();
    formData.append('title', title);
    formData.append('report_file', file);

    try {
      setIsUploading(true);
      const response = await apiClient.post<AnalysisItem>('/ai-report-reader/create/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      toast.success('Report analyzed successfully');

      setTitle('');
      setFile(null);
      fetchAnalyses();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to analyze report');
    } finally {
      setIsUploading(false);
    }
  };

  const riskClass = (risk: string) => {
    const v = risk?.toUpperCase();
    if (v === 'CRITICAL') return 'bg-red-100 text-red-800';
    if (v === 'HIGH') return 'bg-orange-100 text-orange-800';
    if (v === 'MODERATE') return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">AI Report Reader</h1>
          <p className="mt-2 text-gray-600">Upload lab reports and generate AI-assisted analysis</p>
        </div>

        <form onSubmit={handleUpload} className="rounded-xl border border-gray-200 bg-white p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Upload New Report</h2>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Optional title (e.g., CBC April 2026)"
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500"
          />
          <input
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900"
            required
          />
          <button
            type="submit"
            disabled={isUploading}
            className="rounded-lg bg-blue-600 px-5 py-2 font-semibold text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isUploading ? 'Analyzing...' : 'Analyze Report'}
          </button>
        </form>

        <div className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Analysis History</h2>

          {isLoading && <p className="text-gray-600">Loading analyses...</p>}

          {!isLoading && analyses.length === 0 && (
            <p className="text-gray-600">No AI analyses found yet.</p>
          )}

          {!isLoading && analyses.length > 0 && (
            <div className="space-y-3">
              {analyses.map((item) => (
                <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">{item.title || `Analysis #${item.id}`}</h3>
                      <p className="text-sm text-gray-600">{item.report_type} • {new Date(item.created_at).toLocaleString()}</p>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${riskClass(item.risk_level)}`}>
                      {item.risk_level}
                    </span>
                  </div>
                  <div className="mt-3 flex items-center justify-between">
                    <p className="text-sm text-gray-600 line-clamp-1">{item.recommendations || 'No recommendations provided.'}</p>
                    <Link href={`/ai-health/report-reader/${item.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-700">
                      View
                    </Link>
                  </div>
                  <div className="mt-3 rounded-md border border-blue-100 bg-blue-50 p-3">
                    <p className="text-xs font-semibold uppercase tracking-wide text-blue-800">AI Summary</p>
                    <p className="mt-1 text-sm text-blue-900 line-clamp-3">
                      {item.ai_summary || 'Summary not available for this report.'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
