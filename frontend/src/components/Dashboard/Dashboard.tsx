'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks';
import { AppIcon } from '@/components/UI/AppIcon';

interface DashboardStats {
  total_patients: number;
  total_appointments: number;
  pending_appointments: number;
  total_doctors: number;
}

interface DashboardExtra {
  lab_tests: number;
  prescriptions: number;
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
  total_paid: number;
  total_unpaid: number;
  paid_count: number;
  unpaid_count: number;
  overdue_count: number;
}

interface MetricCard {
  title: string;
  value: string | number;
  description: string;
  href: string;
  icon: React.ComponentProps<typeof AppIcon>['name'];
  tone: string;
}

const toneClasses: Record<string, string> = {
  teal: 'border-teal-200 bg-teal-50/90 text-teal-900',
  cyan: 'border-cyan-200 bg-cyan-50/90 text-cyan-900',
  amber: 'border-amber-200 bg-amber-50/90 text-amber-900',
  rose: 'border-rose-200 bg-rose-50/90 text-rose-900',
  indigo: 'border-indigo-200 bg-indigo-50/90 text-indigo-900',
  slate: 'border-slate-200 bg-slate-50/90 text-slate-900',
};

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
  const [recommendedTests, setRecommendedTests] = useState<LabRecommendationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { userRole: authUserRole, isLoading: isAuthLoading } = useAuth();
  const userRole = (authUserRole || 'patient').toUpperCase();

  useEffect(() => {
    if (isAuthLoading) {
      return;
    }

    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        const role = userRole.toLowerCase();
        const extraData: DashboardExtra = {
          lab_tests: 0,
          prescriptions: 0,
          recommended_tests: 0,
          heart_risk: 'Not Assessed',
          unread_notifications: 0,
        };

        await apiClient.get<DashboardStats>('/dashboard/stats/').then(setStats).catch(() => undefined);

        const requests: Promise<unknown>[] = [
          apiClient.get<{ count: number }>('/lab/bookings/').then((d) => { extraData.lab_tests = d.count || 0; }).catch(() => undefined),
          apiClient.get<{ count: number }>('/prescriptions/').then((d) => { extraData.prescriptions = d.count || 0; }).catch(() => undefined),
          apiClient.get<PaymentStats>('/payments/stats/').then(setPaymentStats).catch(() => setPaymentStats(null)),
          apiClient.get<{ unread_count: number }>('/notifications/unread-count/').then((d) => { extraData.unread_notifications = d.unread_count || 0; }).catch(() => undefined),
          apiClient.get<{ results?: LabRecommendationItem[] }>('/lab/recommendations/?page_size=5').then((d) => {
            const items = d.results || [];
            setRecommendedTests(items);
            extraData.recommended_tests = items.length;
          }).catch(() => setRecommendedTests([])),
        ];

        if (role === 'patient') {
          requests.push(
            apiClient.get<{ count: number; results?: AppointmentSummaryItem[] }>('/appointments/?page_size=200').then((d) => {
              const items = d.results || [];
              const upcoming = items.filter((item) => ['PENDING', 'CONFIRMED'].includes((item.status || '').toUpperCase())).length;
              setRoleStats((prev) => ({ ...prev, my_appointments: d.count || items.length, upcoming_appointments: upcoming }));
            }).catch(() => undefined),
            apiClient.get<{ count: number }>('/prescriptions/').then((d) => {
              setRoleStats((prev) => ({ ...prev, my_prescriptions: d.count || 0 }));
            }).catch(() => undefined),
            apiClient.get<{ count: number }>('/lab/bookings/').then((d) => {
              setRoleStats((prev) => ({ ...prev, my_lab_bookings: d.count || 0 }));
            }).catch(() => undefined)
          );
        }

        if (['patient', 'doctor'].includes(role)) {
          requests.push(
            apiClient.get<{ risk_level: string | null }>('/heart-risk/latest/').then((d) => {
              extraData.heart_risk = d.risk_level || 'Not Assessed';
            }).catch(() => undefined)
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

    void fetchDashboardData();
  }, [isAuthLoading, userRole]);

  const isAdmin = userRole === 'ADMIN';
  const isReceptionist = userRole === 'RECEPTIONIST';
  const isAdminOpsRole = isAdmin || isReceptionist;

  const spotlightCards = useMemo<MetricCard[]>(() => {
    if (userRole === 'PATIENT') {
      return [
        { title: 'My Appointments', value: roleStats.my_appointments, description: 'All care visits on record', href: '/appointments', icon: 'appointments', tone: 'teal' },
        { title: 'Upcoming Visits', value: roleStats.upcoming_appointments, description: 'Pending or confirmed visits', href: '/appointments', icon: 'dashboard', tone: 'amber' },
        { title: 'My Prescriptions', value: roleStats.my_prescriptions, description: 'Active medication plans', href: '/prescriptions', icon: 'prescriptions', tone: 'indigo' },
        { title: 'Unread Alerts', value: extra.unread_notifications, description: 'Messages requiring attention', href: '/notifications', icon: 'notifications', tone: 'rose' },
      ];
    }

    return [
      { title: 'Patients', value: stats.total_patients, description: 'Profiles currently managed', href: '/patients', icon: 'patients', tone: 'teal' },
      { title: 'Appointments', value: stats.total_appointments, description: 'Scheduled care activity', href: '/appointments', icon: 'appointments', tone: 'cyan' },
      { title: 'Pending Workload', value: stats.pending_appointments, description: 'Pending plus confirmed visits', href: '/appointments?filter=ACTIVE', icon: 'dashboard', tone: 'amber' },
      { title: 'Doctors', value: stats.total_doctors, description: 'Active doctor profiles', href: '/doctors', icon: 'doctors', tone: 'indigo' },
    ];
  }, [extra.unread_notifications, roleStats, stats, userRole]);

  const operationsCards = useMemo<MetricCard[]>(() => {
    const cards: MetricCard[] = [
      { title: 'Lab Volume', value: extra.lab_tests, description: 'Bookings and result workflow', href: '/lab-reports', icon: 'lab', tone: 'rose' },
      { title: 'Prescriptions', value: extra.prescriptions, description: 'Medication orders in system', href: '/prescriptions', icon: 'prescriptions', tone: 'amber' },
      { title: userRole === 'PATIENT' ? 'My Lab Bookings' : 'Lab Bookings', value: userRole === 'PATIENT' ? roleStats.my_lab_bookings : extra.lab_tests, description: userRole === 'PATIENT' ? 'Track tests and reports' : 'Current lab workload', href: '/lab-reports', icon: 'lab', tone: 'indigo' },
      { title: 'Heart Risk', value: extra.heart_risk, description: 'Latest risk classification', href: '/ai-health/heart-risk', icon: 'heart', tone: 'teal' },
    ];

    return cards;
  }, [extra.lab_tests, extra.heart_risk, extra.prescriptions, roleStats.my_lab_bookings, userRole]);

  const adminKpis = useMemo<MetricCard[]>(() => {
    if (!isAdminOpsRole || !paymentStats) {
      return [];
    }

    return [
      { title: 'Paid Bills', value: paymentStats.paid_count, description: `Rs. ${Number(paymentStats.total_paid).toFixed(2)} collected`, href: '/billing?status=PAID', icon: 'billing', tone: 'teal' },
      { title: 'Unpaid Bills', value: paymentStats.unpaid_count, description: `Rs. ${Number(paymentStats.total_unpaid).toFixed(2)} pending`, href: '/billing?status=UNPAID', icon: 'finance', tone: 'rose' },
      { title: 'Overdue Bills', value: paymentStats.overdue_count, description: 'Accounts needing follow-up', href: '/billing?status=OVERDUE', icon: 'security', tone: 'amber' },
    ];
  }, [isAdminOpsRole, paymentStats]);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-teal-700/20 border-t-teal-700" />
          <p className="text-sm font-medium text-slate-600">Loading operational dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(15,118,110,0.12),rgba(255,255,255,0.9)_42%,rgba(197,139,42,0.12))] p-8 shadow-[0_22px_70px_rgba(15,23,42,0.08)]">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal-200 bg-white/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-teal-700">
              <AppIcon name="spark" className="h-4 w-4" />
              Production Workspace
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-slate-950">
              {isAdmin ? 'Hospital Command Center' : userRole === 'PATIENT' ? 'Your Care Dashboard' : 'Operations Dashboard'}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
              {isAdminOpsRole
                ? 'Monitor patient flow, diagnostics, billing, and approvals from one polished control surface.'
                : userRole === 'PATIENT'
                  ? 'Track appointments, prescriptions, tests, and notifications in one calm patient workspace.'
                  : 'Stay on top of appointments, records, diagnostics, and care coordination without jumping between modules.'}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/profile" className="inline-flex text-black-600 items-center gap-2 rounded-2xl border border-gray-500 px-5 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5">
              <AppIcon name="profile" className="h-4 w-4" />
              My Profile
            </Link>
            <Link href={isAdminOpsRole ? '/reports' : '/appointments'} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:border-teal-200 hover:text-teal-700">
              <AppIcon name={isAdminOpsRole ? 'reports' : 'appointments'} className="h-4 w-4" />
              {isAdminOpsRole ? 'Open Reports' : 'Open Appointments'}
            </Link>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        {spotlightCards.map((card) => (
          <MetricLinkCard key={card.title} card={card} />
        ))}
      </section>

      {adminKpis.length > 0 && (
        <section className="rounded-[2rem] border border-slate-200 bg-white/88 p-6 shadow-sm">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Financial Snapshot</h2>
              <p className="text-sm text-slate-600">Realtime billing and revenue signals for operations leadership.</p>
            </div>
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
              {isAdmin ? 'Admin' : 'Operations'}
            </span>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {adminKpis.map((card) => (
              <MetricLinkCard key={card.title} card={card} compact />
            ))}
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-4">
        {operationsCards.map((card) => (
          <MetricLinkCard key={card.title} card={card} />
        ))}
      </section>

      {isAdminOpsRole && (
        <section className="rounded-[2rem] border border-slate-200 bg-white/88 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-slate-900">Admin Hub</h2>
          <p className="mt-1 text-sm text-slate-600">The highest-value actions for daily hospital operations.</p>
          <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <QuickActionCard title="Add Doctor" description="Create a new doctor profile." href="/admin/doctors-management?create=1" icon="doctors" />
            <QuickActionCard title="Manage Doctors" description="Review staffing and availability." href="/admin/doctors-management" icon="doctors" />
            <QuickActionCard title="Patient Operations" description="Search, export, and review patient activity." href="/admin/patient-operations" icon="patients" />
            <QuickActionCard title="Billing Overview" description="Review payment history and overdue balances." href="/billing" icon="billing" />
            <QuickActionCard title="Lab Workflow" description="Open lab bookings and results." href="/admin/lab-workflow" icon="lab" />
            <QuickActionCard title="Reports" description="Open the shared operational reports workspace." href="/reports" icon="reports" />
            <QuickActionCard title="Security Monitoring" description="Review logins, lockouts, and access events." href="/admin/security-monitoring" icon="security" />
          </div>
        </section>
      )}

      {userRole === 'PATIENT' && (
        <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <ContentPanel title="Recommended Tests" actionHref="/lab-reports" actionLabel="View all">
            {recommendedTests.length === 0 ? (
              <p className="text-sm text-slate-600">No recommended tests right now.</p>
            ) : (
              <div className="space-y-3">
                {recommendedTests.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4">
                    <div className="flex items-center gap-3">
                      <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-teal-700 shadow-sm">
                        <AppIcon name="lab" className="h-5 w-5" />
                      </span>
                      <div>
                        <p className="font-semibold text-slate-900">{item.test_name}</p>
                        <p className="text-sm text-slate-600">Priority: {item.priority} • Status: {item.status}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ContentPanel>

          <ContentPanel title="Care Alerts" actionHref="/notifications" actionLabel="Open alerts">
            {extra.unread_notifications === 0 ? (
              <p className="text-sm text-slate-600">No new alerts. You are all caught up.</p>
            ) : (
              <div className="rounded-2xl border border-rose-200 bg-rose-50/80 p-4">
                <p className="font-semibold text-rose-900">Unread notifications</p>
                <p className="mt-1 text-sm text-rose-700">You have {extra.unread_notifications} unread update(s).</p>
              </div>
            )}
          </ContentPanel>
        </section>
      )}

      <section>
        <h2 className="text-xl font-bold text-slate-900">Quick Actions</h2>
        <p className="mt-1 text-sm text-slate-600">Jump directly into the workflows that matter most for your role.</p>
        <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {userRole === 'PATIENT' ? (
            <>
              <QuickActionCard title="Appointments" description="Schedule or manage your visits." href="/appointments" icon="appointments" />
              <QuickActionCard title="Medical Records" description="Review your health records." href="/medical-records" icon="reports" />
              <QuickActionCard title="Lab Reports" description="Track bookings and results." href="/lab-reports" icon="lab" />
              <QuickActionCard title="Prescriptions" description="See active medication plans." href="/prescriptions" icon="prescriptions" />
              <QuickActionCard title="Billing" description="Review your invoices and payments." href="/billing" icon="billing" />
              <QuickActionCard title="Notifications" description="Open all care alerts." href="/notifications" icon="notifications" />
              <QuickActionCard title="Doctors" description="Browse available doctors." href="/doctors" icon="doctors" />
              <QuickActionCard title="Heart Risk" description="Run or review your heart risk assessment." href="/ai-health/heart-risk" icon="heart" />
            </>
          ) : (
            <>
              <QuickActionCard title="Appointments" description="Schedule and manage visit flow." href="/appointments" icon="appointments" />
              <QuickActionCard title="Medical Records" description="Review health records and notes." href="/medical-records" icon="reports" />
              <QuickActionCard title="Lab Reports" description="Open tests and diagnostic reports." href="/lab-reports" icon="lab" />
              <QuickActionCard title="Prescriptions" description="Manage medication orders." href="/prescriptions" icon="prescriptions" />
              <QuickActionCard title="Reports" description="Open the shared operational reports workspace." href="/reports" icon="reports" />
              <QuickActionCard title="Doctors" description="View doctor roster and availability." href="/doctors" icon="doctors" />
              <QuickActionCard title="AI Triage" description="Check symptom urgency quickly." href="/ai-health/triage" icon="spark" />
              <QuickActionCard title="My Profile" description="Edit your account details." href="/profile" icon="profile" />
            </>
          )}
        </div>
      </section>
    </div>
  );
}

function MetricLinkCard({ card, compact = false }: { card: MetricCard; compact?: boolean }) {
  return (
    <Link
      href={card.href}
      className={`group rounded-[1.75rem] border ${compact ? 'p-5' : 'p-6'} shadow-sm transition hover:-translate-y-1 hover:shadow-md ${toneClasses[card.tone] || toneClasses.slate}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold">{card.title}</p>
          <p className="mt-3 text-3xl font-extrabold tracking-tight">{card.value}</p>
          <p className="mt-2 text-sm opacity-80">{card.description}</p>
        </div>
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/80 shadow-sm">
          <AppIcon name={card.icon} className="h-5 w-5" />
        </span>
      </div>
    </Link>
  );
}

function QuickActionCard({
  title,
  description,
  href,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  icon: React.ComponentProps<typeof AppIcon>['name'];
}) {
  return (
    <Link href={href} className="group rounded-[1.75rem] border border-slate-200 bg-white/88 p-5 shadow-sm transition hover:-translate-y-1 hover:border-teal-200 hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-semibold text-slate-900 transition group-hover:text-teal-700">{title}</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
        </div>
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-50 text-slate-700 transition group-hover:bg-teal-50 group-hover:text-teal-700">
          <AppIcon name={icon} className="h-5 w-5" />
        </span>
      </div>
    </Link>
  );
}

function ContentPanel({
  title,
  actionHref,
  actionLabel,
  children,
}: {
  title: string;
  actionHref: string;
  actionLabel: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-[2rem] border border-slate-200 bg-white/88 p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-bold text-slate-900">{title}</h2>
        <Link href={actionHref} className="text-sm font-semibold text-teal-700 transition hover:text-teal-800">
          {actionLabel}
        </Link>
      </div>
      {children}
    </div>
  );
}
