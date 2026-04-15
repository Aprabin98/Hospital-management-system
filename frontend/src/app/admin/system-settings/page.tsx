'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';

interface SystemSettings {
  hospitalName: string;
  hospitalEmail: string;
  hospitalPhone: string;
  hospitalAddress: string;
  maxAppointmentsPerDay: number;
  appointmentSlotDuration: number;
  cancellationNoticeHours: number;
  maxConcurrentUsers: number;
  maintenanceMode: boolean;
  autoBackupEnabled: boolean;
  backupFrequencyDays: number;
  enableTwoFactor: boolean;
  enableNotifications: boolean;
}

const DEFAULT_SETTINGS: SystemSettings = {
  hospitalName: 'Hospital Management System',
  hospitalEmail: 'admin@hospital.com',
  hospitalPhone: '+91-XXXXXXXXXX',
  hospitalAddress: '123 Medical Street, City',
  maxAppointmentsPerDay: 50,
  appointmentSlotDuration: 30,
  cancellationNoticeHours: 2,
  maxConcurrentUsers: 100,
  maintenanceMode: false,
  autoBackupEnabled: true,
  backupFrequencyDays: 1,
  enableTwoFactor: true,
  enableNotifications: true,
};

export default function SystemSettingsPage() {
  const [userRole, setUserRole] = useState('');
  const [settings, setSettings] = useState<SystemSettings>(DEFAULT_SETTINGS);
  const [hasChanges, setHasChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
      // Load settings from localStorage (in real app, would fetch from backend)
      const savedSettings = localStorage.getItem('systemSettings');
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings));
      }
    }
  }, []);

  const handleSettingChange = (key: keyof SystemSettings, value: SystemSettings[keyof SystemSettings]) => {
    setSettings((prev) => ({
      ...prev,
      [key]: value,
    }));
    setHasChanges(true);
  };

  const handleSaveSettings = async () => {
    try {
      setIsSaving(true);
      // In real app, would send to backend API
      localStorage.setItem('systemSettings', JSON.stringify(settings));
      setHasChanges(false);
      toast.success('Settings saved successfully');
    } catch {
      toast.error('Failed to save settings');
    } finally {
      setIsSaving(false);
    }
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
          <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
          <p className="mt-2 text-gray-600">Configure hospital system parameters and preferences</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Settings Panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Hospital Information */}
            <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900">Hospital Information</h2>
              <div className="mt-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Hospital Name</label>
                  <input
                    type="text"
                    value={settings.hospitalName}
                    onChange={(e) => handleSettingChange('hospitalName', e.target.value)}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Email</label>
                    <input
                      type="email"
                      value={settings.hospitalEmail}
                      onChange={(e) => handleSettingChange('hospitalEmail', e.target.value)}
                      className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">Phone</label>
                    <input
                      type="tel"
                      value={settings.hospitalPhone}
                      onChange={(e) => handleSettingChange('hospitalPhone', e.target.value)}
                      className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Address</label>
                  <textarea
                    value={settings.hospitalAddress}
                    onChange={(e) => handleSettingChange('hospitalAddress', e.target.value)}
                    rows={3}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </section>

            {/* Appointment Settings */}
            <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900">Appointment Settings</h2>
              <div className="mt-4 space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Max Appointments/Day
                    </label>
                    <input
                      type="number"
                      min="1"
                      value={settings.maxAppointmentsPerDay}
                      onChange={(e) => handleSettingChange('maxAppointmentsPerDay', parseInt(e.target.value))}
                      className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Slot Duration (minutes)
                    </label>
                    <input
                      type="number"
                      min="15"
                      step="15"
                      value={settings.appointmentSlotDuration}
                      onChange={(e) => handleSettingChange('appointmentSlotDuration', parseInt(e.target.value))}
                      className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Cancellation Notice (hours)
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={settings.cancellationNoticeHours}
                      onChange={(e) => handleSettingChange('cancellationNoticeHours', parseInt(e.target.value))}
                      className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>
            </section>

            {/* System Settings */}
            <section className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
              <h2 className="text-xl font-bold text-gray-900">System Configuration</h2>
              <div className="mt-4 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Max Concurrent Users
                  </label>
                  <input
                    type="number"
                    min="1"
                    value={settings.maxConcurrentUsers}
                    onChange={(e) => handleSettingChange('maxConcurrentUsers', parseInt(e.target.value))}
                    className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="space-y-3">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.autoBackupEnabled}
                      onChange={(e) => handleSettingChange('autoBackupEnabled', e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm font-medium text-gray-700">Enable Auto Backup</span>
                  </label>

                  {settings.autoBackupEnabled && (
                    <div className="ml-6">
                      <label className="block text-sm font-medium text-gray-700">
                        Backup Frequency (days)
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={settings.backupFrequencyDays}
                        onChange={(e) => handleSettingChange('backupFrequencyDays', parseInt(e.target.value))}
                        className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  )}

                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.maintenanceMode}
                      onChange={(e) => handleSettingChange('maintenanceMode', e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm font-medium text-gray-700">Maintenance Mode</span>
                  </label>

                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.enableTwoFactor}
                      onChange={(e) => handleSettingChange('enableTwoFactor', e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm font-medium text-gray-700">
                      Enable Two-Factor Authentication
                    </span>
                  </label>

                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={settings.enableNotifications}
                      onChange={(e) => handleSettingChange('enableNotifications', e.target.checked)}
                      className="rounded border-gray-300"
                    />
                    <span className="text-sm font-medium text-gray-700">Enable Notifications</span>
                  </label>
                </div>
              </div>
            </section>
          </div>

          {/* Sidebar: Info & Actions */}
          <div className="space-y-6">
            {/* Status Card */}
            <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
              <h3 className="font-semibold text-blue-900">Current Status</h3>
              <div className="mt-3 space-y-2 text-sm text-blue-800">
                <div className="flex justify-between">
                  <span>Maintenance Mode:</span>
                  <span className="font-medium">
                    {settings.maintenanceMode ? '🔴 ON' : '🟢 OFF'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Two-Factor Auth:</span>
                  <span className="font-medium">
                    {settings.enableTwoFactor ? '✓ Enabled' : '✗ Disabled'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Notifications:</span>
                  <span className="font-medium">
                    {settings.enableNotifications ? '✓ Enabled' : '✗ Disabled'}
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              <h3 className="font-semibold text-gray-900">Configuration Summary</h3>
              <div className="mt-3 space-y-2 text-sm text-gray-700">
                <div className="flex justify-between">
                  <span>Slot Duration:</span>
                  <span className="font-medium">{settings.appointmentSlotDuration} min</span>
                </div>
                <div className="flex justify-between">
                  <span>Max Appointments:</span>
                  <span className="font-medium">{settings.maxAppointmentsPerDay}/day</span>
                </div>
                <div className="flex justify-between">
                  <span>Cancellation Notice:</span>
                  <span className="font-medium">{settings.cancellationNoticeHours} hours</span>
                </div>
                <div className="flex justify-between">
                  <span>Max Users Online:</span>
                  <span className="font-medium">{settings.maxConcurrentUsers}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2">
              <button
                onClick={handleSaveSettings}
                disabled={!hasChanges || isSaving}
                className="w-full rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                onClick={() => {
                  setSettings(DEFAULT_SETTINGS);
                  setHasChanges(false);
                }}
                className="w-full rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
              >
                Reset to Default
              </button>
            </div>

            {/* Help Section */}
            <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
              <h3 className="font-semibold text-yellow-900">💡 Help</h3>
              <ul className="mt-3 space-y-2 text-sm text-yellow-800">
                <li>• Slot duration affects appointment booking</li>
                <li>• Maintenance mode hides system from users</li>
                <li>• 2FA adds security for authentication</li>
                <li>• Auto backup protects your data</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
