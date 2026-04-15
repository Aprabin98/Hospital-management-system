'use client';

import React, { useMemo, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import { useAuth } from '@/hooks';

interface SidebarProps {
  isOpen: boolean;
}

interface NavItem {
  name: string;
  href: string;
  icon: string;
  roles: string[];
}

const navItems: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊', roles: ['admin', 'doctor', 'patient', 'receptionist', 'lab_technician'] },
  { name: 'Manage Doctors', href: '/admin/doctors-management', icon: '👨‍⚕️', roles: ['admin'] },
  { name: 'Manage Tests', href: '/admin/manage-tests', icon: '🧪', roles: ['admin'] },
  { name: 'Specializations', href: '/admin/specializations', icon: '🧬', roles: ['admin'] },
  { name: 'Shifts', href: '/admin/shifts', icon: '🕒', roles: ['admin'] },
  { name: 'Schedules', href: '/admin/schedules', icon: '🗓️', roles: ['admin'] },
  { name: 'Manage Rooms', href: '/admin/rooms-management', icon: '🏨', roles: ['admin'] },
  { name: 'Revenue Summary', href: '/admin/revenue-summary', icon: '💰', roles: ['admin'] },
  { name: 'Drug Interactions', href: '/admin/drug-interactions', icon: '⚗️', roles: ['admin'] },
  { name: 'Lab Workflow', href: '/admin/lab-workflow', icon: '🧫', roles: ['admin'] },
  { name: 'Insurance Verification', href: '/admin/insurance-verification', icon: '🛡️', roles: ['admin', 'receptionist'] },
  { name: 'Waiting & No-Show', href: '/admin/queue-ops', icon: '⏱️', roles: ['admin', 'receptionist'] },
  { name: 'Room Statistics', href: '/admin/room-analytics', icon: '📈', roles: ['admin'] },
  { name: 'Approvals Center', href: '/admin/approvals-center', icon: '✅', roles: ['admin', 'receptionist'] },
  { name: 'Patient Operations', href: '/admin/patient-operations', icon: '👥', roles: ['admin', 'receptionist'] },
  { name: 'Users Management', href: '/admin/users-management', icon: '🔐', roles: ['admin'] },
  { name: 'System Settings', href: '/admin/system-settings', icon: '⚙️', roles: ['admin'] },
  { name: 'Analytics', href: '/admin/analytics', icon: '📊', roles: ['admin'] },
  { name: 'Security Monitoring', href: '/admin/security-monitoring', icon: '🛡️', roles: ['admin'] },
  { name: 'RBAC Verification', href: '/admin/rbac-verification', icon: '🔑', roles: ['admin'] },
  { name: 'System Health', href: '/admin/system-health', icon: '💚', roles: ['admin'] },
  { name: 'Patients', href: '/patients', icon: '👥', roles: ['admin', 'doctor', 'receptionist'] },
  { name: 'Appointments', href: '/appointments', icon: '📅', roles: ['admin', 'doctor', 'patient', 'receptionist'] },
  { name: 'Notifications', href: '/notifications', icon: '🔔', roles: ['admin', 'doctor', 'patient', 'receptionist', 'lab_technician'] },
  { name: 'Billing', href: '/billing', icon: '💳', roles: ['patient', 'admin', 'receptionist'] },
  { name: 'Rooms', href: '/rooms', icon: '🛏️', roles: ['doctor', 'patient', 'receptionist'] },
  { name: 'Manage Leaves', href: '/manage-leaves', icon: '🏖️', roles: ['doctor'] },
  { name: 'Reports', href: '/reports', icon: '📑', roles: ['doctor', 'admin', 'receptionist'] },
  { name: 'Audit Logs', href: '/audit-logs', icon: '🛡️', roles: ['admin'] },
  { name: 'Heart Risk Detector', href: '/ai-health/heart-risk', icon: '❤️', roles: ['doctor', 'patient'] },
  { name: 'AI Report Reader', href: '/ai-health/report-reader', icon: '📄', roles: ['doctor', 'patient', 'receptionist'] },
  { name: 'AI Triage', href: '/ai-health/triage', icon: '🩺', roles: ['doctor', 'patient', 'receptionist'] },
  { name: 'Issued Prescriptions', href: '/prescriptions-writer', icon: '🧾', roles: ['doctor'] },
  { name: 'Doctors', href: '/doctors', icon: '👨‍⚕️', roles: ['doctor', 'patient', 'receptionist'] },
  { name: 'Settings', href: '/settings', icon: '⚙️', roles: ['doctor', 'patient', 'receptionist', 'lab_technician'] },
];

const defaultNavSections = [
  {
    id: 'admin',
    label: 'Admin',
    icon: '🛡️',
    items: ['Dashboard', 'Manage Tests', 'Specializations', 'Shifts', 'Schedules', 'Revenue Summary', 'Drug Interactions', 'Lab Workflow', 'Insurance Verification', 'Waiting & No-Show', 'Room Statistics', 'Audit Logs'],
  },
  {
    id: 'core',
    label: 'Core',
    icon: '🏠',
    items: ['Notifications', 'Settings', 'Billing'],
  },
  {
    id: 'clinical',
    label: 'Clinical',
    icon: '🩺',
    items: ['Patients', 'Appointments', 'Medical Records', 'Prescriptions', 'Issued Prescriptions', 'Manage Leaves', 'Doctors'],
  },
  {
    id: 'diagnostics',
    label: 'Diagnostics',
    icon: '🧪',
    items: ['Lab Reports', 'Reports', 'Reviews', 'My Ratings'],
  },
  {
    id: 'ai',
    label: 'AI Tools',
    icon: '🤖',
    items: ['Heart Risk Detector', 'AI Report Reader', 'AI Triage'],
  },
  {
    id: 'operations',
    label: 'Operations',
    icon: '🏥',
    items: ['Patient Operations', 'Rooms', 'Audit Logs'],
  },
];

const adminNavSections = [
  {
    id: 'overview',
    label: 'Overview',
    icon: '📊',
    items: ['Dashboard'],
  },
  {
    id: 'finance',
    label: 'Finance',
    icon: '💰',
    items: ['Revenue Summary', 'Billing'],
  },
  {
    id: 'management',
    label: 'Management',
    icon: '🧰',
    items: ['Manage Doctors', 'Manage Tests', 'Manage Rooms', 'Specializations', 'Shifts', 'Schedules'],
  },
  {
    id: 'operations',
    label: 'Operations',
    icon: '🏥',
    items: ['Patient Operations', 'Patients', 'Appointments', 'Billing', 'Notifications'],
  },
  {
    id: 'workflow',
    label: 'Workflow',
    icon: '⚙️',
    items: ['Lab Workflow', 'Insurance Verification', 'Waiting & No-Show', 'Room Statistics', 'Approvals Center', 'Reports'],
  },
  {
    id: 'system',
    label: 'System',
    icon: '🛠️',
    items: ['Users Management', 'System Settings', 'Analytics', 'Security Monitoring', 'RBAC Verification', 'System Health', 'Audit Logs'],
  },
];

export default function Sidebar({ isOpen }: SidebarProps) {
  const pathname = usePathname();
  const { userRole } = useAuth();
  const [expanded, setExpanded] = useState<Record<string, boolean>>({
    overview: true,
    finance: true,
    management: true,
    system: false,
    workflow: true,
    admin: true,
    core: true,
    clinical: true,
    diagnostics: true,
    ai: true,
    operations: true,
    other: true,
  });

  const filteredNavItems = userRole
    ? navItems.filter((item) => item.roles.includes(userRole.toLowerCase()))
    : navItems; // Show all items if role not loaded yet (prevents flash of empty sidebar)

  const groupedNav = useMemo(() => {
    const sections = userRole?.toLowerCase() === 'admin' ? adminNavSections : defaultNavSections;

    const grouped = sections.map((section) => ({
      ...section,
      nav: filteredNavItems.filter((item) => section.items.includes(item.name)),
    }));

    // Admin users should see admin controls first in the sidebar hierarchy.
    if (userRole?.toLowerCase() === 'admin') {
      grouped.sort((a, b) => {
        const order = ['overview', 'finance', 'management', 'operations', 'workflow', 'system'];
        const aIndex = order.indexOf(a.id);
        const bIndex = order.indexOf(b.id);
        if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;
        return 0;
      });
    }

    const mappedNames = new Set(sections.flatMap((section) => section.items));
    const otherItems = filteredNavItems.filter((item) => !mappedNames.has(item.name));

    if (otherItems.length > 0) {
      grouped.push({
        id: 'other',
        label: 'Other',
        icon: '📁',
        items: [],
        nav: otherItems,
      });
    }

    return grouped.filter((section) => section.nav.length > 0);
  }, [filteredNavItems, userRole]);

  const toggleSection = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <aside
      className={clsx(
        'bg-slate-800 text-white transition-all duration-300 ease-in-out flex flex-col',
        isOpen ? 'w-64' : 'w-20'
      )}
    >
      <div className="flex h-16 items-center justify-center border-b border-slate-700 shrink-0">
        {isOpen ? (
          <div className="flex items-center gap-2">
            <span className="text-2xl">🏥</span>
            <h1 className="text-xl font-bold text-white">HMS</h1>
          </div>
        ) : (
          <span className="text-2xl">🏥</span>
        )}
      </div>

      <nav className="flex-1 p-3 overflow-y-auto">
        {!isOpen && (
          <div className="space-y-1">
            {filteredNavItems.map((item) => {
              const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
              return (
                <Link
                  key={`${item.href}-${item.name}`}
                  href={item.href}
                  className={clsx(
                    'flex items-center justify-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-600 text-white shadow-sm'
                      : 'text-gray-300 hover:bg-slate-700 hover:text-white'
                  )}
                  title={item.name}
                >
                  <span className="text-lg shrink-0">{item.icon}</span>
                </Link>
              );
            })}
          </div>
        )}

        {isOpen && (
          <div className="space-y-3">
            {groupedNav.map((section) => (
              <div key={section.id} className="rounded-lg bg-slate-900/30">
                <button
                  type="button"
                  onClick={() => toggleSection(section.id)}
                  className="w-full flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-300 hover:text-white"
                >
                  <span className="flex items-center gap-2">
                    <span>{section.icon}</span>
                    <span>{section.label}</span>
                  </span>
                  <span>{expanded[section.id] ? '−' : '+'}</span>
                </button>

                {expanded[section.id] && (
                  <div className="space-y-1 px-2 pb-2">
                    {section.nav.map((item) => {
                      const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
                      return (
                        <Link
                          key={`${item.href}-${item.name}`}
                          href={item.href}
                          className={clsx(
                            'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                            isActive
                              ? 'bg-blue-600 text-white shadow-sm'
                              : 'text-gray-300 hover:bg-slate-700 hover:text-white'
                          )}
                        >
                          <span className="text-lg shrink-0">{item.icon}</span>
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

      {/* Version tag */}
      {isOpen && (
        <div className="p-4 border-t border-slate-700">
          <p className="text-xs text-slate-500 text-center">HMS v1.0</p>
        </div>
      )}
    </aside>
  );
}
