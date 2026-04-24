'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { useAuth } from '@/hooks';
import { AppIcon } from '@/components/UI/AppIcon';
import { ROUTE_ACCESS } from '@/lib/access';
import { normalizeRole } from '@/lib/auth';

interface SidebarProps {
  isOpen: boolean;
}

interface NavItem {
  name: string;
  href: string;
  roles: string[];
}

const navItems: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', roles: ['admin', 'doctor', 'patient', 'receptionist', 'lab_technician', 'nurse'] },
  { name: 'Manage Doctors', href: '/admin/doctors-management', roles: ['admin'] },
  { name: 'Manage Tests', href: '/admin/manage-tests', roles: ['admin'] },
  { name: 'Specializations', href: '/admin/specializations', roles: ['admin'] },
  { name: 'Shifts', href: '/admin/shifts', roles: ['admin'] },
  { name: 'Schedules', href: '/admin/schedules', roles: ['admin'] },
  { name: 'Manage Rooms', href: '/admin/rooms-management', roles: ['admin'] },
  { name: 'Revenue Summary', href: '/admin/revenue-summary', roles: ['admin'] },
  { name: 'Drug Interactions', href: '/admin/drug-interactions', roles: ['admin'] },
  { name: 'Lab Workflow', href: '/admin/lab-workflow', roles: ['admin'] },
  { name: 'Insurance Verification', href: '/admin/insurance-verification', roles: ['admin', 'receptionist'] },
  { name: 'Waiting & No-Show', href: '/admin/queue-ops', roles: ['admin', 'receptionist'] },
  { name: 'Reception Queue', href: '/receptionist/queue', roles: ['admin', 'receptionist', 'doctor'] },
  { name: 'Nurse Dashboard', href: '/nurse/dashboard', roles: ['nurse', 'admin', 'doctor'] },
  { name: 'Room Statistics', href: '/admin/room-analytics', roles: ['admin'] },
  { name: 'Approvals Center', href: '/admin/approvals-center', roles: ['admin', 'receptionist'] },
  { name: 'Patient Operations', href: '/admin/patient-operations', roles: ['admin', 'receptionist'] },
  { name: 'Users Management', href: '/admin/users-management', roles: ['admin'] },
  { name: 'System Settings', href: '/admin/system-settings', roles: ['admin'] },
  { name: 'Analytics', href: '/admin/analytics', roles: ['admin'] },
  { name: 'Security Monitoring', href: '/admin/security-monitoring', roles: ['admin'] },
  { name: 'RBAC Verification', href: '/admin/rbac-verification', roles: ['admin'] },
  { name: 'System Health', href: '/admin/system-health', roles: ['admin'] },
  { name: 'Patients', href: '/patients', roles: ['admin', 'doctor', 'receptionist', 'nurse'] },
  { name: 'Appointments', href: '/appointments', roles: ['admin', 'doctor', 'patient', 'receptionist', 'nurse'] },
  { name: 'Medical Records', href: '/medical-records', roles: ['admin', 'doctor', 'patient', 'receptionist', 'nurse'] },
  { name: 'Prescriptions', href: '/prescriptions', roles: ['admin', 'doctor', 'patient', 'receptionist', 'nurse', 'pharmacist'] },
  { name: 'Notifications', href: '/notifications', roles: ['admin', 'doctor', 'patient', 'receptionist', 'lab_technician', 'nurse'] },
  { name: 'Billing', href: '/billing', roles: ['patient', 'admin', 'receptionist'] },
  { name: 'Lab Reports', href: '/lab-reports', roles: ['admin', 'doctor', 'patient', 'receptionist', 'lab_technician'] },
  { name: 'Reviews', href: '/reviews', roles: ['admin', 'doctor', 'patient', 'receptionist'] },
  { name: 'My Ratings', href: '/my-ratings', roles: ['patient'] },
  { name: 'Rooms', href: '/rooms', roles: ['doctor', 'patient', 'receptionist'] },
  { name: 'Manage Leaves', href: '/manage-leaves', roles: ['doctor'] },
  { name: 'Reports', href: '/reports', roles: ['doctor', 'admin', 'receptionist'] },
  { name: 'Audit Logs', href: '/audit-logs', roles: ['admin'] },
  { name: 'Heart Risk Detector', href: '/ai-health/heart-risk', roles: ['doctor', 'patient'] },
  { name: 'AI Report Reader', href: '/ai-health/report-reader', roles: ['doctor', 'patient', 'receptionist'] },
  { name: 'AI Triage', href: '/ai-health/triage', roles: ['doctor', 'patient', 'receptionist', 'nurse'] },
  { name: 'Issued Prescriptions', href: '/prescriptions-writer', roles: ['doctor'] },
  { name: 'Doctors', href: '/doctors', roles: ['doctor', 'patient', 'receptionist', 'nurse'] },
  { name: 'Settings', href: '/settings', roles: ['doctor', 'patient', 'receptionist', 'lab_technician', 'nurse'] },
  { name: 'Lab Samples', href: '/lab/samples', roles: ['admin', 'lab_technician'] },
  { name: 'QC Logs', href: '/lab/qc-logs', roles: ['admin', 'lab_technician'] },
  { name: 'Critical Lab Values', href: '/lab/critical-values', roles: ['admin', 'doctor', 'lab_technician'] },
  { name: 'Pharmacy Dashboard', href: '/pharmacy/dashboard', roles: ['admin', 'pharmacist'] },
  { name: 'Pending Dispense', href: '/pharmacy/dispense', roles: ['admin', 'pharmacist'] },
  { name: 'Medication Inventory', href: '/pharmacy/inventory', roles: ['admin', 'pharmacist'] },
  { name: 'IPD Patients', href: '/ipd', roles: ['admin', 'doctor', 'nurse', 'receptionist'] },
  { name: 'Doctor IPD Rounds', href: '/ipd/doctor-rounds', roles: ['admin', 'doctor'] },
  { name: 'Emergency', href: '/emergency', roles: ['admin', 'doctor', 'nurse', 'receptionist'] },
  { name: 'Radiology Dashboard', href: '/radiology', roles: ['admin', 'doctor', 'nurse', 'receptionist', 'lab_technician'] },
  { name: 'Imaging History', href: '/radiology/history', roles: ['admin', 'doctor', 'receptionist', 'patient'] },
  { name: 'Finance Dashboard', href: '/finance/dashboard', roles: ['admin', 'billing_officer', 'insurance_coordinator'] },
  { name: 'Compliance Center', href: '/compliance', roles: ['admin', 'quality_compliance_officer'] },
];

const defaultNavSections = [
  { id: 'core', label: 'Core', items: ['Dashboard', 'Notifications', 'Settings'] },
  { id: 'clinical', label: 'Clinical', items: ['Patients', 'Appointments', 'Medical Records', 'Prescriptions', 'Doctors', 'Manage Leaves', 'Issued Prescriptions'] },
  { id: 'diagnostics', label: 'Diagnostics', items: ['Lab Reports', 'Lab Samples', 'QC Logs', 'Critical Lab Values', 'Radiology Dashboard', 'Imaging History', 'Pharmacy Dashboard', 'Pending Dispense', 'Medication Inventory'] },
  { id: 'operations', label: 'Operations', items: ['Reception Queue', 'Nurse Dashboard', 'Rooms', 'IPD Patients', 'Doctor IPD Rounds', 'Emergency', 'Reports', 'Reviews', 'My Ratings', 'Billing'] },
  { id: 'intelligence', label: 'AI & Quality', items: ['Heart Risk Detector', 'AI Report Reader', 'AI Triage', 'Finance Dashboard', 'Compliance Center'] },
];

const adminNavSections = [
  { id: 'overview', label: 'Overview', items: ['Dashboard', 'Analytics', 'Reports'] },
  { id: 'management', label: 'Management', items: ['Manage Doctors', 'Manage Tests', 'Specializations', 'Shifts', 'Schedules', 'Manage Rooms', 'Users Management', 'System Settings'] },
  { id: 'operations', label: 'Operations', items: ['Patient Operations', 'Patients', 'Appointments', 'Reception Queue', 'Approvals Center', 'Waiting & No-Show', 'Insurance Verification', 'Room Statistics', 'Emergency', 'Billing'] },
  { id: 'clinical', label: 'Clinical', items: ['Medical Records', 'Prescriptions', 'Doctors', 'Nurse Dashboard', 'IPD Patients', 'Doctor IPD Rounds'] },
  { id: 'platform', label: 'Platform', items: ['Revenue Summary', 'Lab Workflow', 'Lab Samples', 'QC Logs', 'Critical Lab Values', 'Radiology Dashboard', 'Pharmacy Dashboard', 'Medication Inventory', 'Drug Interactions', 'Notifications'] },
  { id: 'security', label: 'Security', items: ['Security Monitoring', 'RBAC Verification', 'System Health', 'Audit Logs', 'Compliance Center'] },
];

const sectionIcons: Record<string, React.ComponentProps<typeof AppIcon>['name']> = {
  overview: 'dashboard',
  management: 'users',
  operations: 'emergency',
  clinical: 'heart',
  diagnostics: 'lab',
  intelligence: 'spark',
  platform: 'radiology',
  security: 'security',
  core: 'dashboard',
};

const itemIcons: Record<string, React.ComponentProps<typeof AppIcon>['name']> = {
  Dashboard: 'dashboard',
  Patients: 'patients',
  'Patient Operations': 'patients',
  Appointments: 'appointments',
  Doctors: 'doctors',
  'Manage Doctors': 'doctors',
  Billing: 'billing',
  'Revenue Summary': 'finance',
  'Finance Dashboard': 'finance',
  'Lab Reports': 'lab',
  'Lab Samples': 'lab',
  'Lab Workflow': 'lab',
  'QC Logs': 'lab',
  'Critical Lab Values': 'lab',
  Prescriptions: 'prescriptions',
  'Issued Prescriptions': 'prescriptions',
  Rooms: 'rooms',
  'Manage Rooms': 'rooms',
  'Room Statistics': 'rooms',
  Notifications: 'notifications',
  Reports: 'reports',
  Analytics: 'analytics',
  Settings: 'settings',
  'System Settings': 'settings',
  'Users Management': 'users',
  'Security Monitoring': 'security',
  'RBAC Verification': 'security',
  'System Health': 'security',
  'Audit Logs': 'security',
  Emergency: 'emergency',
  'Radiology Dashboard': 'radiology',
  'Imaging History': 'radiology',
  'Pharmacy Dashboard': 'pharmacy',
  'Pending Dispense': 'pharmacy',
  'Medication Inventory': 'pharmacy',
  'IPD Patients': 'ipd',
  'Doctor IPD Rounds': 'ipd',
  'Heart Risk Detector': 'heart',
  'AI Report Reader': 'spark',
  'AI Triage': 'spark',
  'Compliance Center': 'compliance',
};

const syncedNavItems = navItems.map((item) => ({
  ...item,
  roles: (ROUTE_ACCESS[item.href] ?? item.roles).map((role) => normalizeRole(role).toLowerCase()),
}));

export default function Sidebar({ isOpen }: SidebarProps) {
  const pathname = usePathname();
  const currentPath = pathname || '';
  const { userRole } = useAuth();
  const normalizedRole = (userRole || '').toLowerCase();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    overview: true,
    management: true,
    operations: true,
    clinical: true,
    diagnostics: true,
    intelligence: true,
    platform: true,
    security: false,
    core: true,
    other: true,
  });

  const filteredNavItems = useMemo(
    () => (normalizedRole ? syncedNavItems.filter((item) => item.roles.includes(normalizedRole)) : []),
    [normalizedRole]
  );

  const groupedNav = useMemo(() => {
    if (!normalizedRole) {
      return [];
    }

    const sections = normalizedRole === 'admin' ? adminNavSections : defaultNavSections;
    const grouped = sections.map((section) => ({
      ...section,
      nav: filteredNavItems.filter((item) => section.items.includes(item.name)),
    }));

    const mappedNames = new Set(sections.flatMap((section) => section.items));
    const otherItems = filteredNavItems.filter((item) => !mappedNames.has(item.name));

    if (otherItems.length > 0) {
      grouped.push({
        id: 'other',
        label: 'Other',
        items: [],
        nav: otherItems,
      });
    }

    return grouped.filter((section) => section.nav.length > 0);
  }, [filteredNavItems, normalizedRole]);

  const toggleSection = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <aside
      className={clsx(
        'flex flex-col border-r border-white/10 bg-[linear-gradient(180deg,#0f172a_0%,#11263a_42%,#0b3a41_100%)] text-white shadow-[14px_0_50px_rgba(2,6,23,0.18)] transition-all duration-300 ease-in-out',
        isOpen ? 'w-72' : 'w-20'
      )}
    >
      <div className="shrink-0 border-b border-white/10 px-4 py-5">
        {isOpen ? (
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-teal-200">
              <AppIcon name="heart" className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-200/90">MediMind</p>
              <h1 className="text-lg font-bold text-white">Hospital OS</h1>
            </div>
          </div>
        ) : (
          <div className="flex justify-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-teal-200">
              <AppIcon name="heart" className="h-6 w-6" />
            </div>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto p-3">
        {!isOpen && (
          <div className="space-y-2">
            {filteredNavItems.map((item) => {
              const isActive = currentPath === item.href || (item.href !== '/dashboard' && currentPath.startsWith(item.href));
              return (
                <Link
                  key={`${item.href}-${item.name}`}
                  href={item.href}
                  className={clsx(
                    'flex items-center justify-center rounded-2xl border px-3 py-3 transition',
                    isActive
                      ? 'border-teal-300/60 bg-teal-400/20 text-white'
                      : 'border-white/5 bg-white/5 text-slate-200 hover:border-white/15 hover:bg-white/10'
                  )}
                  title={item.name}
                >
                  <AppIcon name={itemIcons[item.name] || 'dashboard'} className="h-5 w-5" />
                </Link>
              );
            })}
          </div>
        )}

        {isOpen && (
          <div className="space-y-3">
            {groupedNav.map((section) => (
              <div key={section.id} className="overflow-hidden rounded-3xl border border-white/8 bg-white/5">
                <button
                  type="button"
                  onClick={() => toggleSection(section.id)}
                  className="flex w-full items-center justify-between px-4 py-3 text-left"
                >
                  <span className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-2xl bg-white/10 text-teal-200">
                      <AppIcon name={sectionIcons[section.id] || 'dashboard'} className="h-4 w-4" />
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-200">{section.label}</span>
                  </span>
                  <span className="text-sm text-slate-400">{expanded[section.id] ? '−' : '+'}</span>
                </button>

                {expanded[section.id] && (
                  <div className="space-y-1 px-2 pb-2">
                    {section.nav.map((item) => {
                      const isActive = currentPath === item.href || (item.href !== '/dashboard' && currentPath.startsWith(item.href));
                      return (
                        <Link
                          key={`${item.href}-${item.name}`}
                          href={item.href}
                          className={clsx(
                            'flex items-center gap-3 rounded-2xl px-3 py-2.5 text-sm font-medium transition',
                            isActive
                              ? 'bg-gradient-to-r from-teal-500/25 to-cyan-400/15 text-white'
                              : 'text-slate-200 hover:bg-white/10 hover:text-white'
                          )}
                        >
                          <AppIcon name={itemIcons[item.name] || 'dashboard'} className="h-4 w-4 shrink-0" />
                          <span className="truncate">{item.name}</span>
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </nav>

      {isOpen && (
        <div className="border-t border-white/10 p-4">
          <div className="rounded-3xl border border-teal-400/15 bg-teal-400/10 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-100">Release</p>
            <p className="mt-1 text-sm font-semibold text-white">Production polish applied</p>
            <p className="mt-1 text-xs text-slate-300">Django API, dashboard shell, and navigation streamlined.</p>
          </div>
        </div>
      )}
    </aside>
  );
}
