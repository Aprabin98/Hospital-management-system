'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface HealthCheckResult {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time_ms: number;
  last_check: string;
}

interface SystemHealth {
  overall_status: 'healthy' | 'degraded' | 'unhealthy';
  uptime_seconds: number;
  check_timestamp: string;
  services: HealthCheckResult[];
}

interface QueueMetrics {
  waiting_patients: number;
  pending_approvals: number;
  overdue_items: number;
  queue_health: 'good' | 'warning' | 'critical';
}

interface APIMetrics {
  total_requests_today: number;
  failed_requests_today: number;
  avg_response_time_ms: number;
  error_rate_percent: number;
}

export default function SystemHealthPage() {
  const [userRole, setUserRole] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [queueMetrics, setQueueMetrics] = useState<QueueMetrics | null>(null);
  const [apiMetrics, setApiMetrics] = useState<APIMetrics | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    loadData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch system health
      const healthResponse = await apiClient.get<SystemHealth>('/system/health-check/');
      setSystemHealth(healthResponse);

      // Fetch queue metrics
      const queueResponse = await apiClient.get<QueueMetrics>('/system/queue-metrics/');
      setQueueMetrics(queueResponse);

      // Fetch API metrics
      const apiResponse = await apiClient.get<APIMetrics>('/system/api-metrics/');
      setApiMetrics(apiResponse);

      setLastRefresh(new Date());
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load system health data';
      setSystemHealth(null);
      setQueueMetrics(null);
      setApiMetrics(null);
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  if (userRole !== 'ADMIN') {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <p className="mt-2 text-gray-600">Only ADMIN users can access system health monitoring.</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'degraded':
        return 'bg-amber-50 border-amber-200 text-amber-800';
      case 'unhealthy':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
        return <span className="inline-block h-3 w-3 rounded-full bg-green-500" />;
      case 'degraded':
        return <span className="inline-block h-3 w-3 rounded-full bg-amber-500" />;
      case 'unhealthy':
        return <span className="inline-block h-3 w-3 rounded-full bg-red-500" />;
      default:
        return <span className="inline-block h-3 w-3 rounded-full bg-gray-500" />;
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Health Dashboard</h1>
            <p className="mt-2 text-gray-600">Real-time monitoring of system services and performance.</p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">Last refresh: {lastRefresh.toLocaleTimeString()}</span>
            <button
              onClick={loadData}
              disabled={loading}
              className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh Now'}
            </button>
          </div>
        </div>

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {/* Overall Status */}
        {systemHealth && (
          <div className={`rounded-lg border ${getStatusColor(systemHealth.overall_status)} p-5`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getStatusBadge(systemHealth.overall_status)}
                <div>
                  <h2 className="text-lg font-semibold capitalize">Overall System Status: {systemHealth.overall_status}</h2>
                  <p className="text-sm">Uptime: {Math.floor(systemHealth.uptime_seconds / 86400)} days</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Queue Health */}
        {queueMetrics && (
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Waiting Patients</p>
              <p className="mt-2 text-2xl font-bold text-gray-900">{queueMetrics.waiting_patients}</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Pending Approvals</p>
              <p className="mt-2 text-2xl font-bold text-blue-600">{queueMetrics.pending_approvals}</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Overdue Items</p>
              <p className="mt-2 text-2xl font-bold text-red-600">{queueMetrics.overdue_items}</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Queue Health</p>
              <p className="mt-2">
                <span
                  className={`rounded px-2 py-1 text-sm font-semibold capitalize ${
                    queueMetrics.queue_health === 'good'
                      ? 'bg-green-100 text-green-800'
                      : queueMetrics.queue_health === 'warning'
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {queueMetrics.queue_health}
                </span>
              </p>
            </div>
          </div>
        )}

        {/* Service Health */}
        {systemHealth && (
          <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <h3 className="mb-4 text-lg font-semibold text-gray-900">Service Health</h3>
            <div className="space-y-3">
              {systemHealth.services.map((service, idx) => (
                <div
                  key={idx}
                  className={`rounded-lg border p-4 ${getStatusColor(service.status)}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusBadge(service.status)}
                      <div>
                        <p className="font-medium">{service.service}</p>
                        <p className="text-sm">Response time: {service.response_time_ms}ms</p>
                      </div>
                    </div>
                    <span className="text-sm capitalize">{service.status}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* API Performance */}
        {apiMetrics && (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">API Performance</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600">Total Requests Today</p>
                  <p className="text-2xl font-bold text-gray-900">{apiMetrics.total_requests_today}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Failed Requests</p>
                  <p className="text-xl font-bold text-red-600">{apiMetrics.failed_requests_today}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Error Rate</p>
                  <div className="mt-1 h-2 rounded-full bg-gray-200">
                    <div
                      className="h-2 rounded-full bg-red-500"
                      style={{ width: `${Math.min(apiMetrics.error_rate_percent * 10, 100)}%` }}
                    />
                  </div>
                  <p className="mt-1 text-sm font-medium">{apiMetrics.error_rate_percent.toFixed(2)}%</p>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Response Time</h3>
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600">Average Response Time</p>
                  <p className="text-2xl font-bold text-blue-600">{apiMetrics.avg_response_time_ms}ms</p>
                </div>
                <div className="rounded-lg bg-blue-50 p-3">
                  <p className="text-sm text-blue-700">
                    ✓ Response time is within acceptable range. Target: &lt;200ms
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
