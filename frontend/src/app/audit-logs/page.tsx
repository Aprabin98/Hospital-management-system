'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface AuditLogItem {
  id: number;
  created_at: string;
  action: string;
  actor_email: string;
  actor_role: string;
  model_name: string;
  object_id: string;
  object_repr: string;
  description: string;
  ip_address: string | null;
  path: string;
  method: string;
  metadata: Record<string, unknown>;
}

interface AuditLogsResponse {
  count: number;
  page: number;
  page_size: number;
  results: AuditLogItem[];
}

const ACTIONS = ['', 'LOGIN', 'LOGOUT', 'LOGIN_FAILED', 'CREATE', 'UPDATE', 'DELETE', 'SECURITY', 'OTHER'];
const DATE_PRESETS = ['', 'today', 'last7', 'last30'];

const toInputDate = (value: Date) => value.toISOString().slice(0, 10);

const escapeCsv = (value: string) => `"${value.replace(/"/g, '""')}"`;

const getErrorMessage = (err: unknown, fallback: string) => {
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return fallback;
};

export default function AuditLogsPage() {
  const { userRole } = useAuth();
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [queryFilter, setQueryFilter] = useState('');
  const [datePreset, setDatePreset] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [selectedMetadataLog, setSelectedMetadataLog] = useState<AuditLogItem | null>(null);
  const [exporting, setExporting] = useState(false);
  const [page, setPage] = useState(1);
  const pageSize = 30;

  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(totalCount / pageSize));
  }, [totalCount]);

  useEffect(() => {
    if (!datePreset) {
      return;
    }

    const now = new Date();
    const end = toInputDate(now);
    let start = end;

    if (datePreset === 'last7') {
      const past = new Date(now);
      past.setDate(now.getDate() - 6);
      start = toInputDate(past);
    } else if (datePreset === 'last30') {
      const past = new Date(now);
      past.setDate(now.getDate() - 29);
      start = toInputDate(past);
    }

    setDateFrom(start);
    setDateTo(end);
    setPage(1);
  }, [datePreset]);

  const buildFilterParams = useCallback(
    (targetPage: number, targetPageSize: number): Record<string, string | number> => {
      const params: Record<string, string | number> = {
        page: targetPage,
        page_size: targetPageSize,
      };

      if (actionFilter) {
        params.action = actionFilter;
      }
      if (queryFilter.trim()) {
        params.q = queryFilter.trim();
      }
      if (dateFrom) {
        params.date_from = dateFrom;
      }
      if (dateTo) {
        params.date_to = dateTo;
      }

      return params;
    },
    [actionFilter, queryFilter, dateFrom, dateTo]
  );

  useEffect(() => {
    const fetchAuditLogs = async () => {
      if ((userRole || '').toUpperCase() !== 'ADMIN') {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError('');

        const params = buildFilterParams(page, pageSize);
        const response = await apiClient.get<AuditLogsResponse>('/audit/logs/', { params });
        setLogs(response.results || []);
        setTotalCount(response.count || 0);
      } catch (err: unknown) {
        setError(getErrorMessage(err, 'Failed to load audit logs'));
      } finally {
        setLoading(false);
      }
    };

    fetchAuditLogs();
  }, [userRole, page, pageSize, buildFilterParams]);

  const buildCsvContent = (rows: AuditLogItem[]) => {
    if (rows.length === 0) {
      return '';
    }

    const headers = [
      'id',
      'created_at',
      'action',
      'actor_email',
      'actor_role',
      'model_name',
      'object_id',
      'object_repr',
      'description',
      'ip_address',
      'path',
      'method',
      'metadata_json',
    ];

    const lines = [headers.join(',')];

    for (const log of rows) {
      const row = [
        String(log.id),
        log.created_at || '',
        log.action || '',
        log.actor_email || '',
        log.actor_role || '',
        log.model_name || '',
        log.object_id || '',
        log.object_repr || '',
        log.description || '',
        log.ip_address || '',
        log.path || '',
        log.method || '',
        JSON.stringify(log.metadata || {}),
      ];
      lines.push(row.map((value) => escapeCsv(value)).join(','));
    }

    return lines.join('\n');
  };

  const downloadCsv = (csvContent: string, filename: string) => {
    if (!csvContent) {
      return;
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    window.URL.revokeObjectURL(url);
  };

  const exportCsvCurrentPage = () => {
    const csvContent = buildCsvContent(logs);
    downloadCsv(csvContent, `audit-logs-page-${page}.csv`);
  };

  const exportCsvAllFiltered = async () => {
    if (totalCount === 0 || exporting) {
      return;
    }

    try {
      setExporting(true);

      const allRows: AuditLogItem[] = [];
      const exportPageSize = 100;
      let exportPage = 1;
      let expectedCount = totalCount;

      while (allRows.length < expectedCount && exportPage <= 500) {
        const response = await apiClient.get<AuditLogsResponse>('/audit/logs/', {
          params: buildFilterParams(exportPage, exportPageSize),
        });

        const chunk = response.results || [];
        expectedCount = response.count || expectedCount;
        allRows.push(...chunk);

        if (chunk.length < exportPageSize) {
          break;
        }
        exportPage += 1;
      }

      const csvContent = buildCsvContent(allRows);
      downloadCsv(csvContent, 'audit-logs-filtered-all.csv');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to export filtered logs'));
    } finally {
      setExporting(false);
    }
  };

  const applyDatePreset = (preset: string) => {
    setDatePreset(preset);
    if (!preset) {
      setDateFrom('');
      setDateTo('');
      setPage(1);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.audit}
      title="audit logs"
      description="Audit logs are available only for admin users."
      contentClassName="space-y-4"
    >
      <div className="space-y-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Audit Logs</h1>
          <p className="mt-1 text-gray-600">Track system actions, billing changes, and security events.</p>
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <button
              onClick={() => applyDatePreset('today')}
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${datePreset === 'today' ? 'border-sky-500 bg-sky-50 text-sky-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}
            >
              Today
            </button>
            <button
              onClick={() => applyDatePreset('last7')}
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${datePreset === 'last7' ? 'border-sky-500 bg-sky-50 text-sky-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}
            >
              Last 7 Days
            </button>
            <button
              onClick={() => applyDatePreset('last30')}
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${datePreset === 'last30' ? 'border-sky-500 bg-sky-50 text-sky-700' : 'border-gray-300 text-gray-700 hover:bg-gray-50'}`}
            >
              Last 30 Days
            </button>
            <button
              onClick={() => applyDatePreset('')}
              className="rounded-full border border-gray-300 px-3 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50"
            >
              Clear Date
            </button>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-5">
            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-600">Action</label>
              <select
                value={actionFilter}
                onChange={(e) => {
                  setActionFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                {ACTIONS.map((action) => (
                  <option key={action || 'ALL'} value={action}>
                    {action || 'ALL'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-600">Date Range</label>
              <select
                value={datePreset}
                onChange={(e) => {
                  applyDatePreset(e.target.value);
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                {DATE_PRESETS.map((preset) => (
                  <option key={preset || 'ALL_DATES'} value={preset}>
                    {preset === '' ? 'ALL DATES' : preset === 'today' ? 'TODAY' : preset === 'last7' ? 'LAST 7 DAYS' : 'LAST 30 DAYS'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-600">From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => {
                  setDatePreset('');
                  setDateFrom(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-600">To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => {
                  setDatePreset('');
                  setDateTo(e.target.value);
                  setPage(1);
                }}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>

            <div className="md:col-span-5">
              <label className="mb-1 block text-xs font-semibold uppercase tracking-wide text-gray-600">Search</label>
              <input
                value={queryFilter}
                onChange={(e) => {
                  setQueryFilter(e.target.value);
                  setPage(1);
                }}
                placeholder="Search actor, model, object, path, or description"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>
        )}

        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
            <h2 className="text-lg font-semibold text-gray-900">Events ({totalCount})</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={exportCsvCurrentPage}
                disabled={loading || logs.length === 0 || exporting}
                className="rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Export CSV (Current Page)
              </button>
              <button
                onClick={exportCsvAllFiltered}
                disabled={loading || totalCount === 0 || exporting}
                className="rounded-lg border border-emerald-600 bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {exporting ? 'Exporting...' : 'Export CSV (All Filtered)'}
              </button>
            </div>
          </div>

          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading audit logs...</div>
          ) : logs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No audit events found for current filters.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Time</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Action</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Actor</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Target</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Description</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">IP</th>
                    <th className="px-4 py-3 text-left font-semibold text-gray-600">Metadata</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {logs.map((log) => (
                    <tr key={log.id} className="align-top hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-700">{new Date(log.created_at).toLocaleString()}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        <p className="font-medium">{log.actor_email || 'Anonymous'}</p>
                        <p className="text-xs text-gray-500">{log.actor_role || '-'}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        <p className="font-medium">{log.model_name || '-'}</p>
                        <p className="text-xs text-gray-500">{log.object_id || '-'} {log.object_repr ? `(${log.object_repr})` : ''}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-700">
                        <p>{log.description || '-'}</p>
                        <p className="mt-1 text-xs text-gray-500">{log.method || '-'} {log.path || '-'}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{log.ip_address || '-'}</td>
                      <td className="px-4 py-3 text-gray-700">
                        <button
                          onClick={() => setSelectedMetadataLog(log)}
                          className="rounded-lg border border-gray-300 px-2 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                        >
                          View JSON
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {selectedMetadataLog && (
          <div className="fixed inset-0 z-40">
            <div
              className="absolute inset-0 bg-black/40"
              onClick={() => setSelectedMetadataLog(null)}
            />
            <div className="absolute right-0 top-0 h-full w-full max-w-2xl overflow-auto bg-white shadow-2xl">
              <div className="sticky top-0 flex items-center justify-between border-b border-gray-200 bg-white px-5 py-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Metadata JSON</h3>
                  <p className="text-xs text-gray-600">
                    #{selectedMetadataLog.id} {selectedMetadataLog.action} {selectedMetadataLog.model_name || ''}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedMetadataLog(null)}
                  className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
              </div>
              <div className="space-y-3 p-5">
                <div className="grid grid-cols-1 gap-3 rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700 md:grid-cols-2">
                  <p><span className="font-semibold">Time:</span> {new Date(selectedMetadataLog.created_at).toLocaleString()}</p>
                  <p><span className="font-semibold">Actor:</span> {selectedMetadataLog.actor_email || 'Anonymous'}</p>
                  <p><span className="font-semibold">Action:</span> {selectedMetadataLog.action}</p>
                  <p><span className="font-semibold">Path:</span> {selectedMetadataLog.path || '-'}</p>
                </div>
                <pre className="overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {JSON.stringify(selectedMetadataLog.metadata || {}, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-white p-3 text-sm shadow-sm">
          <p className="text-gray-600">Page {page} of {totalPages}</p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page <= 1}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={page >= totalPages}
              className="rounded-lg border border-gray-300 px-3 py-1.5 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </ProtectedPage>
  );
}
