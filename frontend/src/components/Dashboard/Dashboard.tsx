'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface DashboardStats {
  total_patients: number;
  total_appointments: number;
  pending_appointments: number;
  total_doctors: number;
}

interface DashboardExtra {
  lab_tests: number;
  prescriptions: number;
  room_assignments: number;
  room_recommendations: number;
  recommended_tests: number;
  heart_risk: string;
  unread_notifications: number;
}

interface RoleStats {
  my_appointments: number;
  upcoming_appointments: number;
  my_prescriptions: number;
  my_lab_bookings: number;
}

interface LabRecommendationItem {
  id: number;
  test_name: string;
  priority: string;
  status: string;
}

interface AppointmentSummaryItem {
  status: string;
}

interface PaymentStats {
  total_amount: number;
  total_paid: number;
  total_unpaid: number;
  total_refunded: number;
  payment_count: number;
  paid_count: number;
  unpaid_count: number;
  overdue_count: number;
}

interface AdminKpiCard {
  title: string;
  value: string | number;
  description: string;
  icon: string;
  href: string;
  tone: 'blue' | 'green' | 'amber' | 'violet' | 'rose' | 'slate';
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_patients: 0,
    total_appointments: 0,
    pending_appointments: 0,
    total_doctors: 0,
  });
  const [extra, setExtra] = useState<DashboardExtra>({
    lab_tests: 0,
    prescriptions: 0,
    room_assignments: 0,
    room_recommendations: 0,
    recommended_tests: 0,
    heart_risk: 'Not Assessed',
    unread_notifications: 0,
  });
  const [roleStats, setRoleStats] = useState<RoleStats>({
    my_appointments: 0,
    upcoming_appointments: 0,
    my_prescriptions: 0,
    my_lab_bookings: 0,
  });
  const [paymentStats, setPaymentStats] = useState<PaymentStats | null>(null);
  const [revenueSummary, setRevenueSummary] = useState<{ net_revenue: number; total_refunded_amount: number; pending_refund_count: number } | null>(null);
  const [recommendedTests, setRecommendedTests] = useState<LabRecommendationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userRole, setUserRole] = useState<string>('patient');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);

        // Get role from localStorage
        const role = localStorage.getItem('userRole') || 'patient';
        setUserRole(role.toUpperCase());

        // Fetch main stats
        try {
          const statsData = await apiClient.get<DashboardStats>('/dashboard/stats/');
          setStats(statsData);
        } catch (e) {
          console.error('Failed to fetch stats:', e);
        }

        // Collect extra data in parallel
        const extraData: DashboardExtra = {
          lab_tests: 0,
          prescriptions: 0,
          room_assignments: 0,
          room_recommendations: 0,
          recommended_tests: 0,
          heart_risk: 'Not Assessed',
          unread_notifications: 0,
        };

        const requests: Promise<unknown>[] = [
          apiClient
            .get<{ count: number }>('/lab/bookings/')
            .then((d) => { extraData.lab_tests = d.count || 0; })
            .catch(() => {}),

          apiClient
            .get<{ count: number }>('/prescriptions/')
            .then((d) => { extraData.prescriptions = d.count || 0; })
            .catch(() => {}),

          apiClient
            .get<PaymentStats>('/payments/stats/')
            .then((d) => {
              setPaymentStats(d);
            })
            .catch(() => {
              setPaymentStats(null);
            }),

          apiClient
            .get<{ id: number }>('/rooms/current-assignment/')
            .then(() => { extraData.room_assignments = 1; })
            .catch(() => { extraData.room_assignments = 0; }),

          apiClient
            .get<{ risk_level: string }>('/heart-risk/latest/')
            .then((d) => { extraData.heart_risk = d.risk_level || 'Not Assessed'; })
            .catch(() => { extraData.heart_risk = 'Not Assessed'; }),

          apiClient
            .get<{ unread_count: number }>('/notifications/unread-count/')
            .then((d) => { extraData.unread_notifications = d.unread_count || 0; })
            .catch(() => { extraData.unread_notifications = 0; }),

          apiClient
            .get<{ results?: LabRecommendationItem[] }>('/lab/recommendations/?page_size=5')
            .then((d) => {
              const recs = d.results || [];
              setRecommendedTests(recs);
              extraData.recommended_tests = recs.length;
            })
            .catch(() => {
              setRecommendedTests([]);
            }),

        ];

        if (role.toLowerCase() !== 'patient') {
          requests.push(
            apiClient
              .get<{ results?: AppointmentSummaryItem[] }>('/rooms/admission-requests/?page_size=5')
              .then((d) => {
                extraData.room_recommendations = (d.results || []).length;
              })
              .catch(() => {
                extraData.room_recommendations = 0;
              })
          );
        }

        if (role.toLowerCase() === 'admin') {
          requests.push(
            apiClient
              .get<{ net_revenue: number; total_refunded_amount: number; pending_refund_count: number }>('/payments/revenue/')
              .then((d) => {
                setRevenueSummary(d);
              })
              .catch(() => {
                setRevenueSummary(null);
              })
          );
        } else {
          setRevenueSummary(null);
        }

        if (role.toLowerCase() === 'patient') {
          requests.push(
            apiClient
              .get<{ count: number; results?: AppointmentSummaryItem[] }>('/appointments/?page_size=200')
              .then((d) => {
                const items = d.results || [];
                const upcoming = items.filter((item) => ['PENDING', 'CONFIRMED'].includes((item.status || '').toUpperCase())).length;
                setRoleStats((prev) => ({ ...prev, my_appointments: d.count || items.length, upcoming_appointments: upcoming }));
              })
              .catch(() => {}),
            apiClient
              .get<{ count: number }>('/prescriptions/')
              .then((d) => {
                setRoleStats((prev) => ({ ...prev, my_prescriptions: d.count || 0 }));
              })
              .catch(() => {}),
            apiClient
              .get<{ count: number }>('/lab/bookings/')
              .then((d) => {
                setRoleStats((prev) => ({ ...prev, my_lab_bookings: d.count || 0 }));
              })
              .catch(() => {})
          );
        }

        await Promise.allSettled(requests);

        setExtra({ ...extraData });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        toast.error('Failed to fetch some dashboard data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const isAdmin = userRole === 'ADMIN';
  const isReceptionist = userRole === 'RECEPTIONIST';
  const isAdminOpsRole = isAdmin || isReceptionist;

  const adminKpis = useMemo<AdminKpiCard[]>(() => {
    if (!isAdminOpsRole) {
      return [];
    }

    const kpis: AdminKpiCard[] = [
      {
        title: 'Total Patients',
        value: stats.total_patients,
        description: 'Active patient profiles in the system',
        icon: '👥',
        href: '/patients',
        tone: 'blue',
      },
      {
        title: 'Total Doctors',
        value: stats.total_doctors,
        description: 'Doctors available for appointments',
        icon: '👨‍⚕️',
        href: '/doctors',
        tone: 'violet',
      },
      {
        title: 'Appointments',
        value: stats.total_appointments,
        description: 'All scheduled appointments',
        icon: '📅',
        href: '/appointments?filter=ALL',
        tone: 'green',
      },
      {
        title: 'Pending Workload',
        value: stats.pending_appointments,
        description: 'PENDING + CONFIRMED appointments',
        icon: '⏳',
        href: '/appointments?filter=ACTIVE',
        tone: 'amber',
      },
    ];

    if (paymentStats) {
      kpis.push(
        {
          title: 'Paid Bills',
          value: paymentStats.paid_count,
          description: `Rs. ${Number(paymentStats.total_paid).toFixed(2)} collected`,
          icon: '💸',
          href: '/billing?status=PAID',
          tone: 'green',
        },
        {
          title: 'Unpaid Bills',
          value: paymentStats.unpaid_count,
          description: `Rs. ${Number(paymentStats.total_unpaid).toFixed(2)} pending`,
          icon: '🧾',
          href: '/billing?status=UNPAID',
          tone: 'rose',
        },
        {
          title: 'Overdue Bills',
          value: paymentStats.overdue_count,
          description: 'Payments past due date',
          icon: '⚠️',
          href: '/billing?status=OVERDUE',
          tone: 'amber',
        }
      );
    }

    if (revenueSummary) {
      kpis.push({
        title: 'Net Revenue',
        value: `Rs. ${Number(revenueSummary.net_revenue).toFixed(2)}`,
        description: `Refunded: Rs. ${Number(revenueSummary.total_refunded_amount).toFixed(2)}`,
        icon: '💰',
        href: '/billing',
        tone: 'slate',
      });
    }

    return kpis;
  }, [isAdminOpsRole, paymentStats, revenueSummary, stats]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-600 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className={isAdminOpsRole ? 'rounded-2xl border border-indigo-200 bg-gradient-to-r from-indigo-50 via-blue-50 to-white p-6' : 'flex justify-between items-center'}>
        <div className={isAdminOpsRole ? 'flex justify-between items-center gap-4' : 'flex justify-between items-center'}>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isAdmin ? 'Admin Command Center' : 'Dashboard'}
          </h1>
          <p className="mt-2 text-gray-600">
            {isAdminOpsRole
              ? 'Monitor patient flow, billing, appointments, and operations from one place.'
              : 'Welcome to Hospital Management System'}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href="/profile"
            className="inline-block rounded-lg bg-blue-600 px-4 py-2 font-medium text-white transition-colors hover:bg-blue-700"
          >
            My Profile
          </Link>
          {isAdminOpsRole && (
            <Link
              href="/reports"
              className="inline-block rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 transition-colors hover:bg-gray-50"
            >
              Open Reports
            </Link>
          )}
        </div>
        </div>
      </div>

      {/* Main Stats Grid */}
      {userRole === 'PATIENT' ? (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard title="My Appointments" value={roleStats.my_appointments} icon="📅" color="green" />
          <StatCard title="Upcoming" value={roleStats.upcoming_appointments} icon="⏳" color="yellow" />
          <StatCard title="My Prescriptions" value={roleStats.my_prescriptions} icon="💊" color="blue" />
          <StatCard title="Unread Alerts" value={extra.unread_notifications} icon="🔔" color="purple" />
        </div>
      ) : isAdminOpsRole ? (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Total Patients" value={stats.total_patients} icon="👥" color="blue" />
          <StatCard title="Appointments" value={stats.total_appointments} icon="📅" color="green" />
          <StatCard title="Pending" value={stats.pending_appointments} icon="⏳" color="yellow" />
          <StatCard title="Doctors" value={stats.total_doctors} icon="👨‍⚕️" color="purple" />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Total Patients" value={stats.total_patients} icon="👥" color="blue" />
          <StatCard title="Appointments" value={stats.total_appointments} icon="📅" color="green" />
          <StatCard title="Pending" value={stats.pending_appointments} icon="⏳" color="yellow" />
          <StatCard title="Doctors" value={stats.total_doctors} icon="👨‍⚕️" color="purple" />
        </div>
      )}

      {isAdminOpsRole && adminKpis.length > 0 && (
        <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-gray-900">Admin KPIs</h2>
              <p className="text-sm text-gray-600">Live operational metrics pulled from appointments and billing.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
              {isAdmin ? 'Admin' : 'Operations'}
            </span>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {adminKpis.map((card) => (
              <Link
                key={card.title}
                href={card.href}
                className="group rounded-2xl border border-gray-200 p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
              >
                <div className={
                  {
                    blue: 'bg-blue-50 border-blue-200',
                    green: 'bg-green-50 border-green-200',
                    amber: 'bg-amber-50 border-amber-200',
                    violet: 'bg-violet-50 border-violet-200',
                    rose: 'bg-rose-50 border-rose-200',
                    slate: 'bg-slate-50 border-slate-200',
                  }[card.tone]
                + ' rounded-2xl border p-4'}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-medium text-gray-600">{card.title}</p>
                      <p className="mt-2 text-2xl font-bold text-gray-900">{card.value}</p>
                      <p className="mt-1 text-xs text-gray-500">{card.description}</p>
                    </div>
                    <span className="text-3xl">{card.icon}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Secondary Stats Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        <DashboardLink title="Lab Tests/Reports" icon="🧪" href="/lab-reports" count={extra.lab_tests} color="red" />
        <DashboardLink title="Prescriptions" icon="💊" href="/prescriptions" count={extra.prescriptions} color="orange" />
        <DashboardLink title={userRole === 'PATIENT' ? 'My Lab Bookings' : 'Room Allocation'} icon={userRole === 'PATIENT' ? '🧾' : '🏥'} href={userRole === 'PATIENT' ? '/lab-reports' : '/rooms'} count={userRole === 'PATIENT' ? roleStats.my_lab_bookings : extra.room_assignments} color="indigo" />
        <DashboardLink title="Heart Risk Assessment" icon="❤️" href="/ai-health/heart-risk" status={extra.heart_risk} color="pink" />
      </div>

      {isAdminOpsRole && (
        <div className="space-y-4 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Admin Hub</h2>
            <p className="text-sm text-gray-600">Use these few actions to get to the right place quickly.</p>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <QuickActionCard title="Add Doctor" description="Create a doctor profile" href="/admin/doctors-management?create=1" icon="➕" />
            <QuickActionCard title="Manage Doctors" description="Review and update doctor profiles" href="/admin/doctors-management" icon="👨‍⚕️" />
            <QuickActionCard title="Add Room" description="Create a new room and beds" href="/admin/rooms-management" icon="🏨" />
            <QuickActionCard title="Manage Rooms" description="Review current room inventory" href="/admin/rooms-management" icon="🛏️" />
            <QuickActionCard title="Patient Operations" description="Search, review, and export patient records" href="/admin/patient-operations" icon="👥" />
            <QuickActionCard title="Approvals Center" description="Review admissions, transfers, leaves, and refunds" href="/admin/approvals-center" icon="✅" />
            <QuickActionCard title="Revenue Summary" description="View billing totals and financial summary" href="/admin/revenue-summary" icon="💰" />
            <QuickActionCard title="Security Monitoring" description="Track logins, lockouts, and failed attempts" href="/admin/security-monitoring" icon="🛡️" />
            <QuickActionCard title="Users Management" description="Manage roles and access control" href="/admin/users-management" icon="🔐" />
            <QuickActionCard title="System Settings" description="Configure hospital settings" href="/admin/system-settings" icon="⚙️" />
            <QuickActionCard title="Analytics" description="Review operational analytics" href="/admin/analytics" icon="📊" />
          </div>
        </div>
      )}

      {userRole === 'PATIENT' && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Recommended Tests</h2>
              <Link href="/lab-reports" className="text-sm font-medium text-blue-600 hover:text-blue-700">View All</Link>
            </div>
            {recommendedTests.length === 0 ? (
              <p className="text-sm text-gray-600">No recommended tests yet.</p>
            ) : (
              <div className="space-y-3">
                {recommendedTests.map((item) => (
                  <div key={item.id} className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                    <p className="font-semibold text-gray-900">{item.test_name}</p>
                    <p className="text-sm text-gray-600">Priority: {item.priority} • Status: {item.status}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900">Care Alerts</h2>
              <Link href="/notifications" className="text-sm font-medium text-blue-600 hover:text-blue-700">View All</Link>
            </div>
            {extra.unread_notifications === 0 ? (
              <p className="text-sm text-gray-600">No new alerts. You are all caught up.</p>
            ) : (
              <div className="space-y-3">
                <div className="rounded-lg border border-gray-100 bg-gray-50 p-3">
                  <p className="font-semibold text-gray-900">Unread Notifications</p>
                  <p className="text-sm text-gray-600">You have {extra.unread_notifications} unread notification(s).</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          {userRole === 'PATIENT' ? (
            <>
              <QuickActionCard title="Appointments" description="Schedule or manage your appointments" href="/appointments" icon="📅" />
              <QuickActionCard title="Medical Records" description="View your health records" href="/medical-records" icon="📋" />
              <QuickActionCard title="Lab Reports" description="Check bookings and results" href="/lab-reports" icon="🧪" />
              <QuickActionCard title="Prescriptions" description="View your prescriptions" href="/prescriptions" icon="💊" />
              <QuickActionCard title="Rooms" description="View room assignment and availability" href="/rooms" icon="🛏️" />
              <QuickActionCard title="Reviews" description="Rate completed appointments" href="/reviews" icon="⭐" />
              <QuickActionCard title="Notifications" description="Open your alerts" href="/notifications" icon="🔔" />
              <QuickActionCard title="Doctors" description="View available doctors" href="/doctors" icon="👨‍⚕️" />
              <QuickActionCard title="Heart Risk" description="Heart risk assessment" href="/ai-health/heart-risk" icon="❤️" />
              <QuickActionCard title="AI Report Reader" description="Analyze uploaded reports" href="/ai-health/report-reader" icon="📄" />
              <QuickActionCard title="AI Triage" description="Check symptom urgency" href="/ai-health/triage" icon="🩺" />
              <QuickActionCard title="My Profile" description="Edit profile information" href="/profile" icon="👤" />
            </>
          ) : isAdmin ? (
            <>
              <QuickActionCard title="Manage Doctors" description="Doctor profiles and availability" href="/admin/doctors-management" icon="👨‍⚕️" />
              <QuickActionCard title="Add Doctor" description="Create a doctor profile" href="/admin/doctors-management?create=1" icon="➕" />
              <QuickActionCard title="Manage Rooms" description="Room inventory and bed creation" href="/admin/rooms-management" icon="🏨" />
              <QuickActionCard title="Add Room" description="Create rooms from the admin UI" href="/admin/rooms-management" icon="🛏️" />
              <QuickActionCard title="Patient Operations" description="Search and export patient operations data" href="/admin/patient-operations" icon="👥" />
              <QuickActionCard title="Approvals Center" description="Handle admissions, transfers, leaves, and refunds" href="/admin/approvals-center" icon="✅" />
              <QuickActionCard title="Revenue Summary" description="Open financial summary" href="/admin/revenue-summary" icon="💰" />
              <QuickActionCard title="Security Monitoring" description="Review login lockouts and security events" href="/admin/security-monitoring" icon="🛡️" />
              <QuickActionCard title="Users Management" description="Manage roles and system access" href="/admin/users-management" icon="🔐" />
              <QuickActionCard title="System Settings" description="Configure hospital policies" href="/admin/system-settings" icon="⚙️" />
              <QuickActionCard title="Analytics" description="View hospital performance metrics" href="/admin/analytics" icon="📊" />
              <QuickActionCard title="Appointments" description="Schedule or manage appointments" href="/appointments" icon="📅" />
              <QuickActionCard title="Billing" description="Review payments and dues" href="/billing" icon="💳" />
              <QuickActionCard title="Reports" description="Open operational reporting" href="/reports" icon="📑" />
              <QuickActionCard title="My Profile" description="Edit profile information" href="/profile" icon="👤" />
            </>
          ) : (
            <>
              <QuickActionCard title="Appointments" description="Schedule or manage appointments" href="/appointments" icon="📅" />
              <QuickActionCard title="Medical Records" description="View health records and history" href="/medical-records" icon="📋" />
              <QuickActionCard title="Lab Reports" description="Check lab test results" href="/lab-reports" icon="🧪" />
              <QuickActionCard title="Doctors" description="View available doctors" href="/doctors" icon="👨‍⚕️" />
              <QuickActionCard title="Prescriptions" description="Manage prescriptions" href="/prescriptions" icon="💊" />
              <QuickActionCard title="Health Report" description="Heart risk assessment" href="/ai-health/heart-risk" icon="❤️" />
              <QuickActionCard title="AI Triage" description="Check symptom urgency" href="/ai-health/triage" icon="🩺" />
              <QuickActionCard title="My Profile" description="Edit profile information" href="/profile" icon="👤" />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: string;
  color: 'blue' | 'green' | 'yellow' | 'purple';
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    purple: 'bg-purple-50 border-purple-200',
  };

  return (
    <div className={`rounded-xl border p-6 ${colorClasses[color]} shadow-sm`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
        </div>
        <span className="text-4xl">{icon}</span>
      </div>
    </div>
  );
}

interface DashboardLinkProps {
  title: string;
  icon: string;
  href: string;
  count?: number;
  status?: string;
  color: 'red' | 'orange' | 'indigo' | 'pink';
}

function DashboardLink({ title, icon, href, count, status, color }: DashboardLinkProps) {
  const colorClasses = {
    red: 'bg-red-50 border-red-200 text-red-900 hover:bg-red-100',
    orange: 'bg-orange-50 border-orange-200 text-orange-900 hover:bg-orange-100',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-900 hover:bg-indigo-100',
    pink: 'bg-pink-50 border-pink-200 text-pink-900 hover:bg-pink-100',
  };

  return (
    <Link href={href}>
      <div className={`rounded-xl border p-6 ${colorClasses[color]} shadow-sm transition-all cursor-pointer`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">{title}</p>
            <p className="mt-2 text-2xl font-bold">{count !== undefined ? count : status}</p>
          </div>
          <span className="text-4xl">{icon}</span>
        </div>
      </div>
    </Link>
  );
}

interface QuickActionCardProps {
  title: string;
  description: string;
  href: string;
  icon: string;
}

function QuickActionCard({ title, description, href, icon }: QuickActionCardProps) {
  return (
    <Link href={href}>
      <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-blue-200 transition-all cursor-pointer group">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-semibold text-gray-900 group-hover:text-blue-700 transition-colors">{title}</p>
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          </div>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </Link>
  );
}
