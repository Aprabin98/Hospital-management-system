'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: 'PATIENT' | 'DOCTOR' | 'RECEPTIONIST' | 'LAB_TECHNICIAN' | 'ADMIN';
  is_active: boolean;
  date_joined: string;
}

const ROLE_OPTIONS = [
  { value: 'PATIENT', label: 'Patient', color: 'blue' },
  { value: 'DOCTOR', label: 'Doctor', color: 'green' },
  { value: 'RECEPTIONIST', label: 'Receptionist', color: 'purple' },
  { value: 'LAB_TECHNICIAN', label: 'Lab Technician', color: 'orange' },
  { value: 'ADMIN', label: 'Admin', color: 'red' },
];

export default function UsersManagementPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState<string>('ALL');
  const [filterStatus, setFilterStatus] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');
  const [pageSize] = useState(15);
  const [currentPage, setCurrentPage] = useState(1);
  const [editingUserId, setEditingUserId] = useState<number | null>(null);
  const [editingRole, setEditingRole] = useState<string>('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);

  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setIsLoading(true);
      const firstResponse = await apiClient.get<PaginatedResponse<User>>('/users/?page=1&page_size=100');
      const firstPageUsers = firstResponse.results || [];
      const totalCount = firstResponse.count || firstPageUsers.length;

      if (firstPageUsers.length >= totalCount) {
        setUsers(firstPageUsers);
      } else {
        const pageSize = 100;
        const totalPages = Math.ceil(totalCount / pageSize);
        const remainingPages = Array.from({ length: Math.max(0, totalPages - 1) }, (_, index) => index + 2);

        const remainingResponses = await Promise.all(
          remainingPages.map((page) => apiClient.get<PaginatedResponse<User>>(`/users/?page=${page}&page_size=${pageSize}`))
        );

        const allUsers = [
          ...firstPageUsers,
          ...remainingResponses.flatMap((response) => response.results || []),
        ];
        setUsers(allUsers);
      }
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
      toast.error('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangeRole = async (userId: number, newRole: string) => {
    try {
      await apiClient.patch(`/users/${userId}/`, { role: newRole });
      setUsers((prev) =>
        prev.map((u) =>
          u.id === userId ? { ...u, role: newRole as User['role'] } : u
        )
      );
      setEditingUserId(null);
      toast.success('User role updated successfully');
    } catch {
      toast.error('Failed to update user role');
    }
  };

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await apiClient.patch(`/users/${userId}/`, { is_active: !currentStatus });
      setUsers((prev) =>
        prev.map((u) =>
          u.id === userId ? { ...u, is_active: !currentStatus } : u
        )
      );
      toast.success(`User ${!currentStatus ? 'activated' : 'deactivated'} successfully`);
    } catch {
      toast.error('Failed to update user status');
    }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await apiClient.delete(`/users/${userId}/`);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
      setShowDeleteConfirm(null);
      toast.success('User deleted successfully');
    } catch {
      toast.error('Failed to delete user');
    }
  };

  const filteredUsers = useMemo(() => {
    let result = users;

    // Filter by search term
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (u) =>
          u.email.toLowerCase().includes(term) ||
          u.first_name.toLowerCase().includes(term) ||
          u.last_name.toLowerCase().includes(term) ||
          u.username.toLowerCase().includes(term)
      );
    }

    // Filter by role
    if (filterRole !== 'ALL') {
      result = result.filter((u) => u.role === filterRole);
    }

    // Filter by status
    if (filterStatus === 'ACTIVE') {
      result = result.filter((u) => u.is_active);
    } else if (filterStatus === 'INACTIVE') {
      result = result.filter((u) => !u.is_active);
    }

    return result;
  }, [users, searchTerm, filterRole, filterStatus]);

  const paginatedUsers = useMemo(() => {
    const startIdx = (currentPage - 1) * pageSize;
    return filteredUsers.slice(startIdx, startIdx + pageSize);
  }, [filteredUsers, currentPage, pageSize]);

  const totalPages = Math.ceil(filteredUsers.length / pageSize);

  const getRoleColor = (role: string) => {
    const roleOption = ROLE_OPTIONS.find((r) => r.value === role);
    return roleOption?.color || 'gray';
  };

  const getRoleLabel = (role: string) => {
    const roleOption = ROLE_OPTIONS.find((r) => r.value === role);
    return roleOption?.label || role;
  };

  const getColorClasses = (color: string) => {
    const colors: { [key: string]: string } = {
      blue: 'bg-blue-100 text-blue-800',
      green: 'bg-green-100 text-green-800',
      purple: 'bg-purple-100 text-purple-800',
      orange: 'bg-orange-100 text-orange-800',
      red: 'bg-red-100 text-red-800',
      gray: 'bg-gray-100 text-gray-800',
    };
    return colors[color] || colors.gray;
  };

  if (!isAdmin) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <p className="text-gray-500">You do not have permission to access this page.</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="mt-2 text-gray-600">View, manage roles, and control access for all hospital users</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 rounded-lg bg-white p-4 shadow-sm">
          <input
            type="text"
            placeholder="Search by name, email, or username"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={filterRole}
            onChange={(e) => {
              setFilterRole(e.target.value);
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Roles</option>
            {ROLE_OPTIONS.map((role) => (
              <option key={role.value} value={role.value}>
                {role.label}
              </option>
            ))}
          </select>
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value as 'ALL' | 'ACTIVE' | 'INACTIVE');
              setCurrentPage(1);
            }}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">All Status</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>

        {/* Users Table */}
        {isLoading ? (
          <div className="flex justify-center py-12">
            <div className="text-gray-500">Loading users...</div>
          </div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
        ) : filteredUsers.length === 0 ? (
          <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">
            No users found matching your criteria.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
            <table className="w-full">
              <thead className="border-b border-gray-200 bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">User</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Email</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Role</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Joined</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {paginatedUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="font-medium text-gray-900">
                          {user.first_name} {user.last_name}
                        </p>
                        <p className="text-sm text-gray-500">@{user.username}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">{user.email}</td>
                    <td className="px-6 py-4">
                      {editingUserId === user.id ? (
                        <div className="flex gap-2">
                          <select
                            value={editingRole}
                            onChange={(e) => setEditingRole(e.target.value)}
                            className="rounded border border-gray-300 bg-white px-2 py-1 text-sm text-gray-900"
                          >
                            {ROLE_OPTIONS.map((role) => (
                              <option key={role.value} value={role.value}>
                                {role.label}
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={() =>
                              handleChangeRole(user.id, editingRole)
                            }
                            className="rounded bg-green-100 px-2 py-1 text-sm font-medium text-green-700 hover:bg-green-200"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingUserId(null)}
                            className="rounded bg-gray-100 px-2 py-1 text-sm font-medium text-gray-700 hover:bg-gray-200"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span
                          className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${getColorClasses(
                            getRoleColor(user.role)
                          )}`}
                        >
                          {getRoleLabel(user.role)}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleToggleStatus(user.id, user.is_active)}
                        className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${
                          user.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {user.is_active ? '✓ Active' : '✗ Inactive'}
                      </button>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">
                      {new Date(user.date_joined).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setEditingUserId(user.id);
                            setEditingRole(user.role);
                          }}
                          className="inline-flex rounded border border-blue-300 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700 hover:bg-blue-100"
                        >
                          Change Role
                        </button>
                        <button
                          onClick={() => setShowDeleteConfirm(user.id)}
                          className="inline-flex rounded border border-red-300 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-100"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between rounded-lg bg-white p-4 shadow-sm">
            <div className="text-sm text-gray-600">
              Showing {(currentPage - 1) * pageSize + 1} to {Math.min(currentPage * pageSize, filteredUsers.length)} of{' '}
              {filteredUsers.length} users
            </div>
            <div className="flex gap-2">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Previous
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => i + 1).map((page) => (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`rounded px-2 py-1 text-sm ${
                      currentPage === page
                        ? 'bg-blue-600 text-white'
                        : 'border border-gray-300 text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    {page}
                  </button>
                ))}
              </div>
              <button
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => p + 1)}
                className="rounded border border-gray-300 px-3 py-1 text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-bold text-gray-900">Confirm Delete</h3>
            <p className="mt-2 text-gray-600">
              Are you sure you want to delete this user? This action cannot be undone.
            </p>
            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="rounded border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteUser(showDeleteConfirm)}
                className="rounded bg-red-600 px-4 py-2 font-medium text-white hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}
