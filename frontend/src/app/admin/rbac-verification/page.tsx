'use client';

import React, { useCallback, useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';

interface RoleEndpoint {
  endpoint: string;
  method: string;
  allowed_roles: string[];
  description: string;
}

interface RoleAccessData {
  role: string;
  accessible_endpoints: number;
  total_endpoints: number;
  endpoints: RoleEndpoint[];
}

interface SystemStatus {
  total_active_users: number;
  admin_users: number;
  authenticated_today: number;
  failed_login_attempts: number;
  two_fa_enabled_users: number;
}

export default function RBACVerificationPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeRole, setActiveRole] = useState('ADMIN');
  const [roleData, setRoleData] = useState<RoleAccessData | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [allRoles] = useState(['ADMIN', 'DOCTOR', 'RECEPTIONIST', 'LAB_TECHNICIAN', 'PATIENT']);
  const [searchFilter, setSearchFilter] = useState('');

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Fetch role-specific data
      const roleResponse = await apiClient.get<RoleAccessData>(
        `/rbac/role-matrix/?role=${activeRole}`
      );
      setRoleData(roleResponse);

      // Fetch system status
      const statusResponse = await apiClient.get<SystemStatus>('/system/security-status/');
      setSystemStatus(statusResponse);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load RBAC verification data';
      setRoleData(null);
      setSystemStatus(null);
      setError(message);
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [activeRole]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const filteredEndpoints = roleData?.endpoints.filter(
    (ep) =>
      ep.endpoint.toLowerCase().includes(searchFilter.toLowerCase()) ||
      ep.description.toLowerCase().includes(searchFilter.toLowerCase())
  ) || [];

  const accessPercentage = roleData ? Math.round((roleData.accessible_endpoints / roleData.total_endpoints) * 100) : 0;

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">RBAC Verification Dashboard</h1>
            <p className="mt-2 text-gray-600">View and verify role-based access control configuration.</p>
          </div>
          <button
            onClick={loadData}
            className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Refresh
          </button>
        </div>

        {/* System Status Summary */}
        {systemStatus && (
          <div className="grid gap-4 md:grid-cols-4">
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="mt-2 text-2xl font-bold text-gray-900">{systemStatus.total_active_users}</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Admin Users</p>
              <p className="mt-2 text-2xl font-bold text-blue-600">{systemStatus.admin_users}</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Auth Today</p>
              <p className="mt-2 text-2xl font-bold text-green-600">{systemStatus.authenticated_today}</p>
            </div>
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-gray-600">Failed Logins</p>
              <p className="mt-2 text-2xl font-bold text-red-600">{systemStatus.failed_login_attempts}</p>
            </div>
          </div>
        )}

        {/* Role Selector */}
        <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">Select Role to Verify</h2>
          <div className="flex flex-wrap gap-3">
            {allRoles.map((role) => (
              <button
                key={role}
                onClick={() => setActiveRole(role)}
                className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                  activeRole === role
                    ? 'bg-blue-600 text-white'
                    : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {role}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">
            Loading RBAC data...
          </div>
        ) : error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        ) : roleData ? (
          <>
            {/* Access Summary */}
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <h3 className="mb-4 text-lg font-semibold text-gray-900">Access Summary for {roleData.role}</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Accessible Endpoints</span>
                  <span className="text-lg font-bold text-blue-600">
                    {roleData.accessible_endpoints} / {roleData.total_endpoints}
                  </span>
                </div>
                <div className="h-3 rounded-full bg-gray-200">
                  <div
                    className="h-3 rounded-full bg-blue-500 transition-all"
                    style={{ width: `${accessPercentage}%` }}
                  />
                </div>
                <p className="text-sm text-gray-600">{accessPercentage}% of endpoints accessible to {roleData.role}</p>
              </div>
            </div>

            {/* Endpoint List */}
            <div className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Endpoint Access Rules</h3>
                <input
                  type="text"
                  placeholder="Search endpoints..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="rounded border border-gray-300 px-3 py-2 text-sm text-gray-900"
                />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b border-gray-200 bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Endpoint</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Method</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Description</th>
                      <th className="px-4 py-3 text-left font-semibold text-gray-700">Allowed Roles</th>
                      <th className="px-4 py-3 text-center font-semibold text-gray-700">Access</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {filteredEndpoints.map((endpoint, idx) => {
                      const hasAccess = endpoint.allowed_roles.includes(roleData.role);
                      return (
                        <tr key={idx} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-mono text-xs text-gray-900">{endpoint.endpoint}</td>
                          <td className="px-4 py-3">
                            <span
                              className={`rounded px-2 py-1 text-xs font-semibold ${
                                endpoint.method === 'GET'
                                  ? 'bg-blue-100 text-blue-800'
                                  : endpoint.method === 'POST'
                                  ? 'bg-green-100 text-green-800'
                                  : endpoint.method === 'PUT'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {endpoint.method}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-gray-600">{endpoint.description}</td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1">
                              {endpoint.allowed_roles.map((role) => (
                                <span
                                  key={role}
                                  className={`rounded px-2 py-1 text-xs font-medium ${
                                    role === 'ADMIN'
                                      ? 'bg-red-100 text-red-800'
                                      : role === 'DOCTOR'
                                      ? 'bg-blue-100 text-blue-800'
                                      : role === 'PATIENT'
                                      ? 'bg-green-100 text-green-800'
                                      : role === 'RECEPTIONIST'
                                      ? 'bg-purple-100 text-purple-800'
                                      : 'bg-gray-100 text-gray-800'
                                  }`}
                                >
                                  {role}
                                </span>
                              ))}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span
                              className={`inline-flex h-8 w-8 items-center justify-center rounded-full ${
                                hasAccess
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-red-100 text-red-700'
                              }`}
                            >
                              {hasAccess ? '✓' : '✗'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {filteredEndpoints.length === 0 && (
                <p className="py-8 text-center text-gray-600">No endpoints match your search filter.</p>
              )}
            </div>
          </>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">
            Unable to load RBAC data.
          </div>
        )}
      </div>
    </MainLayout>
  );
}
