'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface AnalysisDetail {
  id: number;
  title: string;
  patient_name?: string;
  report_file?: string;
  report_type: string;
  risk_level: string;
  ai_summary?: string;
  summary_points?: string[];
  recommendations?: string;
  abnormal_flags?: Array<{ marker: string; value: string | number; status: string }>;
  guidance?: {
    food_suggestions?: string[];
    exercise_suggestions?: string[];
    health_tips?: string[];
  };
  disclaimer?: string;
  created_at: string;
}

export default function ReportReaderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReading, setIsReading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setIsLoading(true);
        const response = await apiClient.get<AnalysisDetail>(`/ai-report-reader/${id}/`);
        setAnalysis(response);
      } catch (err: any) {
        toast.error(err?.message || 'Failed to load analysis details');
      } finally {
        setIsLoading(false);
      }
    };
    if (id) load();
  }, [id]);

  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const normalizeSummaryPoints = (raw?: string, points?: string[]) => {
    if (points && points.length > 0) {
      return points;
    }
    return (raw || '')
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean);
  };

  const readSummary = () => {
    if (!analysis || typeof window === 'undefined' || !('speechSynthesis' in window)) {
      toast.error('Read summary is not supported in this browser.');
      return;
    }

    const points = normalizeSummaryPoints(analysis.ai_summary, analysis.summary_points);
    if (points.length === 0) {
      toast.error('No summary available to read.');
      return;
    }

    window.speechSynthesis.cancel();
    const speechText = points
      .map((point, idx) => `${idx + 1}. ${point.replace(/^\d+\.\s*/, '')}`)
      .join(' ');
    const utterance = new SpeechSynthesisUtterance(speechText);
    utterance.onstart = () => setIsReading(true);
    utterance.onend = () => setIsReading(false);
    utterance.onerror = () => {
      setIsReading(false);
      toast.error('Unable to read summary.');
    };
    window.speechSynthesis.speak(utterance);
  };

  const stopReading = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsReading(false);
    }
  };

  const prettifyReportType = (value?: string) => {
    if (!value) return 'General';
    const normalized = value.toUpperCase();
    if (normalized === 'LIVER') return 'Liver Function';
    if (normalized === 'RENAL') return 'Renal Function';
    if (normalized === 'CBC') return 'Complete Blood Count';
    if (normalized === 'DIABETES') return 'Diabetes';
    if (normalized === 'LIPID') return 'Lipid Profile';
    if (normalized === 'THYROID') return 'Thyroid';
    if (normalized === 'GENERAL') return 'General';
    return value;
  };

  const summaryPoints = analysis ? normalizeSummaryPoints(analysis.ai_summary, analysis.summary_points) : [];

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <Link href="/ai-health/report-reader" className="text-blue-600 hover:text-blue-700 font-medium">
            ← Back to AI Report Reader
          </Link>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">AI Report Analysis</h1>
        </div>

        {isLoading && <p className="text-gray-600">Loading analysis...</p>}

        {!isLoading && !analysis && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">Analysis not found.</div>
        )}

        {analysis && (
          <>
            <div className="rounded-xl border border-gray-200 bg-white p-6">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-2xl font-semibold text-gray-900">Analyzed Report Detail</h2>
                  <p className="mt-1 text-sm text-gray-600">{analysis.title || `Analysis #${analysis.id}`}</p>
                </div>
                <div className="flex items-center gap-2">
                  {analysis.report_file && (
                    <a
                      href={analysis.report_file}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
                    >
                      Open Uploaded Report
                    </a>
                  )}
                  <span className="rounded-full bg-blue-100 px-3 py-1 text-sm font-semibold text-blue-800">Risk: {analysis.risk_level}</span>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6">
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <h3 className="text-lg font-semibold text-gray-900">AI Summary</h3>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={readSummary}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    Read Summary
                  </button>
                  {isReading && (
                    <button
                      type="button"
                      onClick={stopReading}
                      className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
                    >
                      Stop
                    </button>
                  )}
                </div>
              </div>
              {summaryPoints.length > 0 ? (
                <ol className="list-decimal space-y-2 pl-5 text-sm text-gray-700">
                  {summaryPoints.map((point, idx) => (
                    <li key={`summary-${idx}`}>{point.replace(/^\d+\.\s*/, '')}</li>
                  ))}
                </ol>
              ) : (
                <p className="text-sm text-gray-600">No summary available.</p>
              )}
              {analysis.recommendations && (
                <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-800">
                  <span className="font-semibold">Recommendations:</span> {analysis.recommendations}
                </div>
              )}
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6">
              <h3 className="mb-3 text-lg font-semibold text-gray-900">Detected Abnormal Flags</h3>
              {analysis.abnormal_flags && analysis.abnormal_flags.length > 0 ? (
                <ul className="space-y-2">
                  {analysis.abnormal_flags.map((flag, idx) => (
                    <li
                      key={`${flag.marker}-${idx}`}
                      className="rounded-lg border border-red-100 bg-red-50 px-3 py-2 text-sm text-red-800"
                    >
                      <span className="font-semibold">{flag.marker}</span>: {flag.value} ({String(flag.status).replace('_', ' ')})
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-gray-700">No major abnormal flags were detected.</p>
              )}
            </div>

            <div className="rounded-xl border border-gray-200 bg-white p-6">
              <h3 className="mb-3 text-lg font-semibold text-gray-900">Report Meta</h3>
              <div className="grid grid-cols-1 gap-3 text-sm text-gray-700 sm:grid-cols-2">
                <div><span className="font-semibold">Patient:</span> {analysis.patient_name || 'N/A'}</div>
                <div><span className="font-semibold">Type:</span> {prettifyReportType(analysis.report_type)}</div>
                <div><span className="font-semibold">Risk:</span> {analysis.risk_level}</div>
                <div><span className="font-semibold">Created:</span> {new Date(analysis.created_at).toLocaleString()}</div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              <div className="rounded-xl border border-gray-200 bg-white p-6">
                <h3 className="mb-3 text-lg font-semibold text-gray-900">Food Suggestions</h3>
                {analysis.guidance?.food_suggestions && analysis.guidance.food_suggestions.length > 0 ? (
                  <ul className="list-disc space-y-2 pl-5 text-sm text-gray-700">
                    {analysis.guidance.food_suggestions.map((item, idx) => (
                      <li key={`food-${idx}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-600">No food suggestions available.</p>
                )}
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-6">
                <h3 className="mb-3 text-lg font-semibold text-gray-900">Exercise Suggestions</h3>
                {analysis.guidance?.exercise_suggestions && analysis.guidance.exercise_suggestions.length > 0 ? (
                  <ul className="list-disc space-y-2 pl-5 text-sm text-gray-700">
                    {analysis.guidance.exercise_suggestions.map((item, idx) => (
                      <li key={`exercise-${idx}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-600">No exercise suggestions available.</p>
                )}
              </div>

              <div className="rounded-xl border border-gray-200 bg-white p-6">
                <h3 className="mb-3 text-lg font-semibold text-gray-900">Health Tips</h3>
                {analysis.guidance?.health_tips && analysis.guidance.health_tips.length > 0 ? (
                  <ul className="list-disc space-y-2 pl-5 text-sm text-gray-700">
                    {analysis.guidance.health_tips.map((item, idx) => (
                      <li key={`tip-${idx}`}>{item}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-600">No health tips available.</p>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-900">
              {analysis.disclaimer ||
                'This report is read and analyzed by trained AI models on real-world style data and may not always be fully accurate. Please show this analysis to a professional licensed doctor before making medical decisions.'}
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
}
