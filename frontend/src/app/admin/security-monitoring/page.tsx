'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface LoginAttemptItem {
  id: number;
  identifier: string;
  failed_count: number;
  last_ip: string | null;
  last_attempt: string | null;
  locked_until: string | null;
  is_locked: boolean;
  status: 'LOCKED' | 'FAILED' | 'CLEAR';
}

interface AuditLogItem {
  id: number;
  created_at: string;
  action: 'LOGIN' | 'LOGOUT' | 'LOGIN_FAILED' | 'CREATE' | 'UPDATE' | 'DELETE' | 'SECURITY' | 'OTHER';
  actor_email: string;
  actor_role: string;
  description: string;
  ip_address: string;
  path: string;
}

interface PaginatedResponse<T> {
  count: number;
  page: number;
  page_size: number;
  results: T[];
  locked_count?: number;
  failed_count?: number;
}

const SECURITY_TONES: Record<LoginAttemptItem['status'], string> = {
  LOCKED: 'bg-red-100 text-red-800',
  FAILED: 'bg-amber-100 text-amber-800',
  CLEAR: 'bg-green-100 text-green-800',
};

export default function SecurityMonitoringPage() {
  const { userRole } = useAuth();
  const [loading, setLoading] = useState(true);
  const [loginAttempts, setLoginAttempts] = useState<LoginAttemptItem[]>([]);
  const [loginFailures, setLoginFailures] = useState<AuditLogItem[]>([]);
  const [securityEvents, setSecurityEvents] = useState<AuditLogItem[]>([]);
  const [summary, setSummary] = useState({ locked: 0, failed: 0, totalAttempts: 0 });

  const isAdmin = (userRole || '').toUpperCase() === 'ADMIN';

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    try {
      setLoading(true);
      const [attemptsRes, failedLogsRes, securityLogsRes] = await Promise.all([
        apiClient.get<PaginatedResponse<LoginAttemptItem>>('/security/login-attempts/?page_size=100'),
        apiClient.get<PaginatedResponse<AuditLogItem>>('/audit/logs/?action=LOGIN_FAILED&page_size=50'),
        apiClient.get<PaginatedResponse<AuditLogItem>>('/audit/logs/?action=SECURITY&page_size=50'),
      ]);

      setLoginAttempts(attemptsRes.results || []);
      setLoginFailures(failedLogsRes.results || []);
      setSecurityEvents(securityLogsRes.results || []);
      setSummary({
        locked: attemptsRes.locked_count || 0,
        failed: attemptsRes.failed_count || 0,
        totalAttempts: attemptsRes.count || 0,
      });
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to load security monitoring data');
    } finally {
      setLoading(false);
    }
  };

  const recentIssues = useMemo(() => loginAttempts.filter((item) => item.status !== 'CLEAR').slice(0, 8), [loginAttempts]);

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.security}
      title="security monitoring"
      description="Security monitoring is restricted to administrators."
    >
      <div className="space-y-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Security Monitoring</h1>
            <p className="mt-2 text-gray-600">Track login lockouts, failed attempts, and security audit events in one place.</p>
          </div>
          <button onClick={loadSecurityData} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
            Refresh
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-gray-500">Locked Accounts</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{summary.locked}</p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-gray-500">Failed Identifiers</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{summary.failed}</p>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-gray-500">Tracked Attempts</p>
            <p className="mt-1 text-3xl font-bold text-gray-900">{summary.totalAttempts}</p>
          </div>
        </div>

        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading security monitoring data...</div>
        ) : (
          <div className="grid gap-6 xl:grid-cols-2">
            <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Login Attempts</h2>
                <span className="text-sm text-gray-500">Admin visibility only</span>
              </div>
              {recentIssues.length === 0 ? (
                <p className="mt-4 text-sm text-gray-600">No failed or locked attempts found.</p>
              ) : (
                <div className="mt-4 space-y-3">
                  {recentIssues.map((item) => (
                    <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold text-gray-900">{item.identifier}</p>
                          <p className="text-sm text-gray-600">IP: {item.last_ip || 'Unknown'}</p>
                          <p className="text-sm text-gray-600">Last attempt: {item.last_attempt ? new Date(item.last_attempt).toLocaleString() : 'N/A'}</p>
                          <p className="text-sm text-gray-600">Locked until: {item.locked_until ? new Date(item.locked_until).toLocaleString() : 'Not locked'}</p>
                        </div>
                        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${SECURITY_TONES[item.status]}`}>{item.status}</span>
                      </div>
                      <p className="mt-2 text-sm text-gray-700">Failed attempts: {item.failed_count}</p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Security Audit Events</h2>
                <Link href="/audit-logs" className="text-sm font-medium text-blue-600 hover:text-blue-800">
                  Open audit logs
                </Link>
              </div>

              <div className="mt-4 space-y-4">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700">Login failures</h3>
                  {loginFailures.length === 0 ? (
                    <p className="mt-2 text-sm text-gray-600">No recent login failures.</p>
                  ) : (
                    <div className="mt-2 space-y-2">
                      {loginFailures.slice(0, 5).map((item) => (
                        <div key={item.id} className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                          <p className="font-medium text-gray-900">{item.actor_email || 'Unknown user'}</p>
                          <p>{item.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-700">Security actions</h3>
                  {securityEvents.length === 0 ? (
                    <p className="mt-2 text-sm text-gray-600">No security audit events found.</p>
                  ) : (
                    <div className="mt-2 space-y-2">
                      {securityEvents.slice(0, 5).map((item) => (
                        <div key={item.id} className="rounded-lg bg-gray-50 p-3 text-sm text-gray-700">
                          <p className="font-medium text-gray-900">{item.actor_email || 'Unknown user'}</p>
                          <p>{item.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </section>
          </div>
        )}
      </div>
    </ProtectedPage>
  );
}
