'use client';

import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface QCLog {
  id: number;
  sample: number | null;
  qc_type: 'CALIBRATION' | 'QUALITY_CONTROL' | 'MAINTENANCE' | 'VALIDATION';
  test_template: number | null;
  test_name: string | null;
  performed_by: number;
  performed_by_name: string | null;
  result: 'PASSED' | 'FAILED' | 'CONDITIONAL';
  details: string;
  reference_value: string;
  actual_value: string;
  deviation: string;
  performed_at: string;
}

interface QCLogsResponse {
  count: number;
  results: QCLog[];
}

const QC_TYPE_ICONS: Record<string, string> = {
  CALIBRATION: '🔧',
  QUALITY_CONTROL: '✓',
  MAINTENANCE: '🛠️',
  VALIDATION: '✔️',
};

const RESULT_COLORS: Record<string, string> = {
  PASSED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  CONDITIONAL: 'bg-yellow-100 text-yellow-800',
};

export default function QCLogsPage() {
  const [logs, setLogs] = useState<QCLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [qcTypeFilter, setQcTypeFilter] = useState<string>('');
  const [resultFilter, setResultFilter] = useState<string>('');
  const [showCreateForm, setShowCreateForm] = useState(false);

  const [formData, setFormData] = useState({
    qc_type: 'QUALITY_CONTROL',
    test_template: '',
    sample: '',
    result: 'PASSED',
    details: '',
    reference_value: '',
    actual_value: '',
    deviation: '',
  });

  const { userRole } = useAuth();
  const role = (userRole || '').toUpperCase();
  const canCreateLogs = ACCESS_MATRIX.labOperations.includes(role as (typeof ACCESS_MATRIX.labOperations)[number]);

  useEffect(() => {
    const run = async () => {
      try {
        setIsLoading(true);
        let url = '/lab/qc-logs/';
        const params: string[] = [];
        if (qcTypeFilter) params.push(`qc_type=${qcTypeFilter}`);
        if (params.length > 0) url += '?' + params.join('&');

        const response = await apiClient.get<QCLogsResponse>(url);
        let filteredLogs = response.results || [];
        if (resultFilter) {
          filteredLogs = filteredLogs.filter(log => log.result === resultFilter);
        }
        setLogs(filteredLogs);
      } catch (error) {
        toast.error('Failed to load QC logs');
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };
    run();
  }, [qcTypeFilter, resultFilter]);

  const handleCreateLog = async () => {
    if (!formData.qc_type || !formData.details) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      const payload = {
        ...formData,
        test_template: formData.test_template ? parseInt(formData.test_template) : null,
        sample: formData.sample ? parseInt(formData.sample) : null,
      };

      const newLog = await apiClient.post<QCLog>('/lab/qc-logs/', payload);
      setLogs([newLog, ...logs]);
      setFormData({
        qc_type: 'QUALITY_CONTROL',
        test_template: '',
        sample: '',
        result: 'PASSED',
        details: '',
        reference_value: '',
        actual_value: '',
        deviation: '',
      });
      setShowCreateForm(false);
      toast.success('QC log created');
    } catch (error) {
      toast.error('Failed to create QC log');
      console.error(error);
    }
  };

  const passedCount = logs.filter(log => log.result === 'PASSED').length;
  const failedCount = logs.filter(log => log.result === 'FAILED').length;
  const conditionalCount = logs.filter(log => log.result === 'CONDITIONAL').length;

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.labOperations}
      title="QC logs"
      description="Quality-control logs are restricted to laboratory operations roles."
    >
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Quality Control Logs</h1>
          <p className="mt-2 text-gray-600">Track calibration, maintenance, and QC checks</p>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <p className="text-sm text-gray-600">Total QC Logs</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{logs.length}</p>
          </div>
          <div className="rounded-lg border border-green-200 bg-green-50 p-4 shadow-sm">
            <p className="text-sm text-green-800">Passed</p>
            <p className="mt-1 text-3xl font-bold text-green-600">{passedCount}</p>
          </div>
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 shadow-sm">
            <p className="text-sm text-red-800">Failed</p>
            <p className="mt-1 text-3xl font-bold text-red-600">{failedCount}</p>
          </div>
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 shadow-sm">
            <p className="text-sm text-yellow-800">Conditional</p>
            <p className="mt-1 text-3xl font-bold text-yellow-600">{conditionalCount}</p>
          </div>
        </div>

        {/* Filters */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-800 mb-3">Filters</h3>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">QC Type</label>
              <select
                value={qcTypeFilter}
                onChange={e => setQcTypeFilter(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="">All Types</option>
                <option value="CALIBRATION">Calibration</option>
                <option value="QUALITY_CONTROL">Quality Control</option>
                <option value="MAINTENANCE">Maintenance</option>
                <option value="VALIDATION">Validation</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Result</label>
              <select
                value={resultFilter}
                onChange={e => setResultFilter(e.target.value)}
                className="w-full rounded border border-gray-300 px-3 py-2"
              >
                <option value="">All Results</option>
                <option value="PASSED">Passed</option>
                <option value="FAILED">Failed</option>
                <option value="CONDITIONAL">Conditional</option>
              </select>
            </div>
          </div>
        </div>

        {/* QC Logs List */}
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="space-y-2 p-4">
            {isLoading ? (
              <p className="text-center text-gray-500">Loading QC logs...</p>
            ) : logs.length === 0 ? (
              <p className="text-center text-gray-500">No QC logs found</p>
            ) : (
              logs.map(log => (
                <div key={log.id} className="rounded border border-gray-200 p-4 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">{QC_TYPE_ICONS[log.qc_type]}</span>
                        <h3 className="font-medium text-gray-900">{log.qc_type}</h3>
                        <span className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${RESULT_COLORS[log.result]}`}>
                          {log.result}
                        </span>
                      </div>

                      <div className="mt-2 grid gap-2 md:grid-cols-3">
                        <div>
                          <p className="text-xs font-medium text-gray-600">Test Template</p>
                          <p className="text-sm text-gray-900">{log.test_name || 'General'}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-600">Performed By</p>
                          <p className="text-sm text-gray-900">{log.performed_by_name || 'System'}</p>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-gray-600">Date</p>
                          <p className="text-sm text-gray-900">{new Date(log.performed_at).toLocaleString()}</p>
                        </div>
                      </div>

                      <div className="mt-3">
                        <p className="text-xs font-medium text-gray-600">Details</p>
                        <p className="text-sm text-gray-700 mt-1">{log.details}</p>
                      </div>

                      {(log.reference_value || log.actual_value || log.deviation) && (
                        <div className="mt-3 grid gap-2 md:grid-cols-3 bg-gray-50 p-2 rounded">
                          {log.reference_value && (
                            <div>
                              <p className="text-xs font-medium text-gray-600">Reference</p>
                              <p className="text-sm font-mono text-gray-900">{log.reference_value}</p>
                            </div>
                          )}
                          {log.actual_value && (
                            <div>
                              <p className="text-xs font-medium text-gray-600">Actual</p>
                              <p className="text-sm font-mono text-gray-900">{log.actual_value}</p>
                            </div>
                          )}
                          {log.deviation && (
                            <div>
                              <p className="text-xs font-medium text-gray-600">Deviation</p>
                              <p className="text-sm font-mono text-gray-900">{log.deviation}</p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Create QC Log Form */}
        {canCreateLogs && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Create New QC Log</h2>
              <button
                onClick={() => setShowCreateForm(!showCreateForm)}
                className="text-indigo-600 hover:underline"
              >
                {showCreateForm ? 'Cancel' : 'New Log'}
              </button>
            </div>

            {showCreateForm && (
              <div className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">QC Type *</label>
                    <select
                      value={formData.qc_type}
                      onChange={e => setFormData({ ...formData, qc_type: e.target.value })}
                      className="w-full rounded border border-gray-300 px-3 py-2"
                    >
                      <option value="QUALITY_CONTROL">Quality Control</option>
                      <option value="CALIBRATION">Calibration</option>
                      <option value="MAINTENANCE">Maintenance</option>
                      <option value="VALIDATION">Validation</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Result *</label>
                    <select
                      value={formData.result}
                      onChange={e => setFormData({ ...formData, result: e.target.value })}
                      className="w-full rounded border border-gray-300 px-3 py-2"
                    >
                      <option value="PASSED">Passed</option>
                      <option value="FAILED">Failed</option>
                      <option value="CONDITIONAL">Conditional Pass</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Details *</label>
                  <textarea
                    value={formData.details}
                    onChange={e => setFormData({ ...formData, details: e.target.value })}
                    className="w-full rounded border border-gray-300 px-3 py-2"
                    rows={3}
                    placeholder="Describe QC check, calibration results, or validation findings"
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Reference Value</label>
                    <input
                      type="text"
                      value={formData.reference_value}
                      onChange={e => setFormData({ ...formData, reference_value: e.target.value })}
                      className="w-full rounded border border-gray-300 px-3 py-2"
                      placeholder="e.g. 100.0"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Actual Value</label>
                    <input
                      type="text"
                      value={formData.actual_value}
                      onChange={e => setFormData({ ...formData, actual_value: e.target.value })}
                      className="w-full rounded border border-gray-300 px-3 py-2"
                      placeholder="e.g. 99.8"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Deviation</label>
                    <input
                      type="text"
                      value={formData.deviation}
                      onChange={e => setFormData({ ...formData, deviation: e.target.value })}
                      className="w-full rounded border border-gray-300 px-3 py-2"
                      placeholder="e.g. ±0.5%"
                    />
                  </div>
                </div>

                <button
                  onClick={handleCreateLog}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                >
                  Create QC Log
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}
