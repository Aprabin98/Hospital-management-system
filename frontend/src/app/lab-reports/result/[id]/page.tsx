'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

const BACKEND_ORIGIN = process.env.NEXT_PUBLIC_API_URL
  ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/?$/, '')
  : 'http://localhost:8000';

function getBackendFileUrl(path?: string | null) {
  if (!path) {
    return '';
  }
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  return `${BACKEND_ORIGIN}${path.startsWith('/') ? '' : '/'}${path}`;
}

export default function ResultDetailsPage() {
  const params = useParams<{ id?: string | string[] }>();
  const resultId = typeof params?.id === 'string' ? params.id : '';
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchResultDetails = useCallback(async () => {
    if (!resultId) {
      setError('Invalid result id');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      const response = await apiClient.get(`/lab/results/${resultId}/`);
      setResult(response);
    } catch (err: any) {
      setError(err?.message || 'Failed to load result details');
      toast.error('Failed to load result details');
    } finally {
      setIsLoading(false);
    }
  }, [resultId]);

  useEffect(() => {
    void fetchResultDetails();
  }, [fetchResultDetails]);

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </MainLayout>
    );
  }

  if (error || !result) {
    return (
      <MainLayout>
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
          {error || 'Result not found'}
        </div>
        <Link href="/lab-reports" className="mt-4 inline-block text-blue-600 hover:text-blue-700">
          ← Back to Lab Reports
        </Link>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <Link href="/lab-reports" className="text-blue-600 hover:text-blue-700 font-medium mb-2 inline-block">
              ← Back to Lab Reports
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Test Result Details</h1>
            <p className="mt-2 text-gray-600">View your test result information</p>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
            <p className="text-sm text-gray-600">Result Status</p>
            <p className={`inline-block rounded-full px-3 py-1 text-sm font-medium mt-2 ${
              result.status === 'RELEASED'
                ? 'bg-green-100 text-green-800'
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {result.status}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
            <p className="text-sm text-gray-600">Result Released</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">
              {result.is_released ? '✓ Yes' : 'Pending'}
            </p>
          </div>

          <div className={`rounded-lg border shadow-sm p-6 ${
            result.has_critical_values
              ? 'border-red-200 bg-red-50'
              : 'border-green-200 bg-green-50'
          }`}>
            <p className={`text-sm ${
              result.has_critical_values ? 'text-red-600' : 'text-green-600'
            }`}>
              Critical Values
            </p>
            <p className={`text-lg font-semibold mt-2 ${
              result.has_critical_values ? 'text-red-900' : 'text-green-900'
            }`}>
              {result.has_critical_values ? '⚠️ Critical' : 'Normal'}
            </p>
          </div>
        </div>

        {/* Main Details */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6 space-y-4">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Result Information</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <p className="text-sm text-gray-600">Test Name</p>
              <p className="text-lg font-semibold text-gray-900">
                {result.booking_info?.template_name}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Test Date</p>
              <p className="text-lg font-semibold text-gray-900">
                {result.booking_info?.date}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Release Date</p>
              <p className="text-lg font-semibold text-gray-900">
                {result.release_date || 'Not yet released'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Reviewed By</p>
              <p className="text-lg font-semibold text-gray-900">
                {result.reviewed_by || 'Pending review'}
              </p>
            </div>
          </div>
        </div>

        {/* Result Data */}
        {result.result_data && (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Test Results</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Parameter</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Value</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Unit</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Reference Range</th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {result.result_data.map((item: any, idx: number) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm text-gray-900">{item.parameter}</td>
                      <td className="px-6 py-4 text-sm text-gray-900 font-semibold">{item.value}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{item.unit}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{item.reference_range}</td>
                      <td className="px-6 py-4 text-sm">
                        <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${
                          item.is_critical
                            ? 'bg-red-100 text-red-800'
                            : item.status === 'Normal'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {item.status || (item.is_critical ? 'Critical' : 'Normal')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Comments */}
        {result.comments && (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Comments</h2>
            <p className="text-gray-700 whitespace-pre-wrap">{result.comments}</p>
          </div>
        )}

        {/* PDF Download */}
        {result.pdf_file && (
          <div className="rounded-lg border border-gray-200 bg-white shadow-sm p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Report Document</h2>
            <div className="flex flex-wrap gap-3">
              <a 
                href={getBackendFileUrl(result.pdf_url || result.pdf_file)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
              >
                📄 View PDF Report
              </a>
              <a
                href={getBackendFileUrl(result.pdf_url || result.pdf_file)}
                download
                className="inline-flex items-center gap-2 px-6 py-2 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700 transition-colors"
              >
                ⬇️ Download PDF Report
              </a>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-4">
          <Link 
            href="/lab-reports"
            className="px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
          >
            Back to Lab Reports
          </Link>
        </div>
      </div>
    </MainLayout>
  );
}
