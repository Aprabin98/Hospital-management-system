'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';
import ProtectedPage from '@/components/Auth/ProtectedPage';
import { AppIcon } from '@/components/UI/AppIcon';
import StatusBadge from '@/components/UI/StatusBadge';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

type LabBooking = {
  id: number;
  patient_name: string;
  template_name: string;
  date: string;
  status: string;
  status_display?: string;
  payment_status: string;
  amount: string | number;
  specimen_id?: string | null;
  expected_report_at?: string | null;
  collected_at?: string | null;
  received_at?: string | null;
  rejected_reason?: string;
  result_id?: number | null;
};

type LabDashboardResponse = {
  count?: number;
  results?: LabBooking[];
};

type LabResultShell = {
  id: number;
};

type WorkflowOption = {
  value: string;
  label: string;
};

const METRIC_TONES: Record<string, string> = {
  teal: 'border-teal-200 bg-teal-50/90 text-teal-900',
  cyan: 'border-cyan-200 bg-cyan-50/90 text-cyan-900',
  amber: 'border-amber-200 bg-amber-50/90 text-amber-900',
  rose: 'border-rose-200 bg-rose-50/90 text-rose-900',
};

function formatLocalDate(date: Date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatDisplayDate(value?: string | null) {
  if (!value) {
    return 'Not set';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatDisplayDateTime(value?: string | null) {
  if (!value) {
    return 'Not set';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function getWorkflowOptions(status: string): WorkflowOption[] {
  switch (status) {
    case 'PENDING':
      return [
        { value: 'SAMPLE_COLLECTED', label: 'Sample Collected' },
        { value: 'REJECTED_SAMPLE', label: 'Reject Sample' },
      ];
    case 'SAMPLE_COLLECTED':
      return [
        { value: 'PROCESSING', label: 'Processing' },
        { value: 'REJECTED_SAMPLE', label: 'Reject Sample' },
      ];
    default:
      return [];
  }
}

function getDefaultWorkflowStatus(status: string) {
  return getWorkflowOptions(status)[0]?.value || status;
}

export default function LabDashboardPage() {
  const router = useRouter();
  const [bookings, setBookings] = useState<LabBooking[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [updatingBookingId, setUpdatingBookingId] = useState<number | null>(null);
  const [openingResultId, setOpeningResultId] = useState<number | null>(null);
  const [statusDrafts, setStatusDrafts] = useState<Record<number, string>>({});
  const [reasonDrafts, setReasonDrafts] = useState<Record<number, string>>({});

  const fetchBookings = useCallback(async () => {
    try {
      setIsRefreshing(true);
      const response = await apiClient.get<LabDashboardResponse>('/lab/bookings/?page_size=200');
      const items = response.results || [];
      setBookings(items);
      setStatusDrafts(
        items.reduce<Record<number, string>>((accumulator, booking) => {
          accumulator[booking.id] = getDefaultWorkflowStatus(booking.status);
          return accumulator;
        }, {})
      );
      setReasonDrafts(
        items.reduce<Record<number, string>>((accumulator, booking) => {
          accumulator[booking.id] = booking.rejected_reason || '';
          return accumulator;
        }, {})
      );
    } catch (error) {
      toast.error('Failed to load lab dashboard');
      console.error('Failed to load lab dashboard', error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void fetchBookings();
  }, [fetchBookings]);

  const todayKey = formatLocalDate(new Date());
  const activeBookings = useMemo(
    () => bookings.filter((booking) => !['COMPLETED', 'CANCELLED'].includes(booking.status)).sort((left, right) => {
      const leftDate = left.date || '';
      const rightDate = right.date || '';
      if (leftDate === rightDate) {
        return left.id - right.id;
      }
      return leftDate.localeCompare(rightDate);
    }),
    [bookings]
  );

  const metrics = useMemo(() => {
    const now = new Date();

    const todayBookings = bookings.filter((booking) => booking.date === todayKey);
    const pendingBookings = bookings.filter((booking) => ['PENDING', 'SAMPLE_COLLECTED', 'PROCESSING'].includes(booking.status));
    const processingBookings = bookings.filter((booking) => booking.status === 'PROCESSING');
    const rejectedBookings = bookings.filter((booking) => booking.status === 'REJECTED_SAMPLE');
    const overdueBookings = bookings.filter((booking) => {
      if (booking.status === 'COMPLETED' || booking.status === 'CANCELLED' || booking.status === 'REJECTED_SAMPLE') {
        return false;
      }
      if (!booking.expected_report_at) {
        return false;
      }
      const deadline = new Date(booking.expected_report_at);
      return !Number.isNaN(deadline.getTime()) && deadline < now;
    });

    return {
      todayBookings: todayBookings.length,
      pendingBookings: pendingBookings.length,
      processingBookings: processingBookings.length,
      rejectedBookings: rejectedBookings.length,
      overdueBookings: overdueBookings.length,
      sampleCollectedBookings: bookings.filter((booking) => booking.status === 'SAMPLE_COLLECTED').length,
    };
  }, [bookings, todayKey]);

  const updateBookingStatus = async (booking: LabBooking) => {
    const allowedOptions = getWorkflowOptions(booking.status);
    if (allowedOptions.length === 0) {
      toast.error('No workflow update is available for this booking.');
      return;
    }

    const nextStatus = (statusDrafts[booking.id] || allowedOptions[0].value).toUpperCase();
    const rejectionReason = (reasonDrafts[booking.id] || '').trim();

    if (nextStatus === 'REJECTED_SAMPLE' && !rejectionReason) {
      toast.error('Please provide a rejection reason.');
      return;
    }

    try {
      setUpdatingBookingId(booking.id);
      const updated = await apiClient.post<LabBooking>(`/lab/bookings/${booking.id}/update-status/`, {
        status: nextStatus,
        rejected_reason: nextStatus === 'REJECTED_SAMPLE' ? rejectionReason : '',
      });
      setBookings((previous) => previous.map((item) => (item.id === updated.id ? { ...item, ...updated } : item)));
      setStatusDrafts((previous) => ({
        ...previous,
        [booking.id]: getDefaultWorkflowStatus(updated.status),
      }));
      setReasonDrafts((previous) => ({
        ...previous,
        [booking.id]: updated.rejected_reason || '',
      }));
      toast.success('Booking updated');
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update booking');
    } finally {
      setUpdatingBookingId(null);
    }
  };

  const openResultEntry = async (booking: LabBooking) => {
    if (booking.status === 'PENDING' && !booking.result_id) {
      toast.error('Collect the sample before starting report entry.');
      return;
    }

    if (booking.result_id) {
      router.push(`/lab-reports/result/${booking.result_id}`);
      return;
    }

    try {
      setOpeningResultId(booking.id);
      const result = await apiClient.post<LabResultShell>(`/lab/bookings/${booking.id}/result/`, {});
      router.push(`/lab-reports/result/${result.id}`);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to start report entry');
    } finally {
      setOpeningResultId(null);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.labOperations}
      title="lab dashboard"
      description="Lab technicians can update sample status, open report entry, and track pending lab work from one control surface."
    >
      <div className="space-y-8">
        <section className="overflow-hidden rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(14,116,144,0.14),rgba(255,255,255,0.94)_44%,rgba(217,119,6,0.14))] p-8 shadow-[0_22px_70px_rgba(15,23,42,0.08)]">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-200 bg-white/75 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-cyan-700">
                <AppIcon name="lab" className="h-4 w-4" />
                Lab Technician Dashboard
              </div>
              <h1 className="text-4xl font-extrabold tracking-tight text-slate-950">Lab Workflow Console</h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
                Keep the lab queue moving, mark samples as collected or processing, reject unusable samples with a reason, and jump directly into report entry.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void fetchBookings()}
                className="inline-flex items-center gap-2 rounded-2xl border border-slate-900 bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-slate-800"
              >
                <AppIcon name="dashboard" className="h-4 w-4" />
                {isRefreshing ? 'Refreshing...' : 'Refresh Lab Queue'}
              </button>
              <Link href="/lab-reports?tab=results" className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 transition hover:-translate-y-0.5 hover:border-cyan-200 hover:text-cyan-700">
                <AppIcon name="reports" className="h-4 w-4" />
                Open Lab Reports
              </Link>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-5 md:grid-cols-3 xl:grid-cols-3">
          <MetricCard title="Today's Bookings" value={metrics.todayBookings} description="Bookings scheduled for today" tone="teal" icon="appointments" />
          <MetricCard title="Total Pending" value={metrics.pendingBookings} description="Open bookings needing lab action" tone="amber" icon="dashboard" />
          <MetricCard title="Overdue Reports" value={metrics.overdueBookings} description="Reports past expected turnaround" tone="rose" icon="security" />
        </section>

        <section className="rounded-[2rem] border border-slate-200 bg-white/92 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Lab Flow Snapshot</h2>
              <p className="mt-1 text-sm text-slate-600">Only lab bookings are shown here, in the same order the team should work them.</p>
            </div>
            <div className="flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
              <span className="rounded-full bg-cyan-50 px-3 py-1 text-cyan-700">Sample Collected {metrics.sampleCollectedBookings}</span>
              <span className="rounded-full bg-amber-50 px-3 py-1 text-amber-700">Processing {metrics.processingBookings}</span>
              <span className="rounded-full bg-rose-50 px-3 py-1 text-rose-700">Rejected {metrics.rejectedBookings}</span>
            </div>
          </div>

          <div className="mt-6 overflow-x-auto rounded-[1.5rem] border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">#ID</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Patient</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Test</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-bold uppercase tracking-[0.18em] text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {isLoading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-16 text-center text-sm text-slate-500">
                      Loading lab bookings...
                    </td>
                  </tr>
                ) : activeBookings.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-16 text-center text-sm text-slate-500">
                      No active lab bookings right now.
                    </td>
                  </tr>
                ) : (
                  activeBookings.map((booking) => {
                    const options = getWorkflowOptions(booking.status);
                    const selectedStatus = statusDrafts[booking.id] || options[0]?.value || booking.status;
                    const canOpenResult = Boolean(booking.result_id) || ['SAMPLE_COLLECTED', 'PROCESSING'].includes(booking.status);

                    return (
                      <tr key={booking.id} className="align-top hover:bg-slate-50/80">
                        <td className="px-4 py-5 text-sm font-semibold text-slate-900">#{booking.id}</td>
                        <td className="px-4 py-5 text-sm text-slate-900">{booking.patient_name}</td>
                        <td className="px-4 py-5 text-sm text-slate-700">{booking.template_name}</td>
                        <td className="px-4 py-5 text-sm text-slate-700">
                          <div className="space-y-1">
                            <p>{formatDisplayDate(booking.date)}</p>
                            <p className="text-xs text-slate-500">Expected {formatDisplayDateTime(booking.expected_report_at)}</p>
                          </div>
                        </td>
                        <td className="px-4 py-5 text-sm">
                          <div className="space-y-2">
                            <StatusBadge value={booking.status_display || booking.status} />
                            {booking.specimen_id ? (
                              <p className="text-xs font-medium text-cyan-700">Specimen {booking.specimen_id}</p>
                            ) : (
                              <p className="text-xs text-slate-500">Specimen not assigned yet</p>
                            )}
                            {booking.rejected_reason ? (
                              <p className="text-xs text-rose-700">Reason: {booking.rejected_reason}</p>
                            ) : null}
                          </div>
                        </td>
                        <td className="px-4 py-5 text-sm">
                          <div className="space-y-4 rounded-[1.25rem] border border-slate-200 bg-slate-50/80 p-4">
                            <div className="flex flex-wrap gap-2">
                              {canOpenResult ? (
                                <button
                                  type="button"
                                  onClick={() => void openResultEntry(booking)}
                                  disabled={openingResultId === booking.id}
                                  className="inline-flex items-center gap-2 rounded-xl border border-cyan-200 bg-white px-3 py-2 text-xs font-semibold text-cyan-700 transition hover:border-cyan-300 hover:bg-cyan-50 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                  <AppIcon name="lab" className="h-4 w-4" />
                                  {openingResultId === booking.id ? 'Opening...' : booking.result_id ? 'Open Results' : 'Start Results'}
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  disabled
                                  className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-100 px-3 py-2 text-xs font-semibold text-slate-400"
                                >
                                  <AppIcon name="lab" className="h-4 w-4" />
                                  Collect sample first
                                </button>
                              )}
                              <Link
                                href={`/lab-reports/booking/${booking.id}`}
                                className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-white"
                              >
                                <AppIcon name="reports" className="h-4 w-4" />
                                Booking Details
                              </Link>
                            </div>

                            {options.length > 0 ? (
                              <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-3">
                                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                                  <select
                                    value={selectedStatus}
                                    onChange={(event) => setStatusDrafts((previous) => ({ ...previous, [booking.id]: event.target.value }))}
                                    className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-cyan-400"
                                  >
                                    {options.map((option) => (
                                      <option key={option.value} value={option.value}>
                                        {option.label}
                                      </option>
                                    ))}
                                  </select>
                                  <button
                                    type="button"
                                    onClick={() => void updateBookingStatus(booking)}
                                    disabled={updatingBookingId === booking.id}
                                    className={`rounded-xl px-4 py-2 text-sm font-semibold text-white transition disabled:cursor-not-allowed disabled:opacity-60 ${getStatusButtonClass(selectedStatus)}`}
                                  >
                                    {updatingBookingId === booking.id ? 'Updating...' : 'Update'}
                                  </button>
                                </div>

                                {selectedStatus === 'REJECTED_SAMPLE' && (
                                  <textarea
                                    value={reasonDrafts[booking.id] || ''}
                                    onChange={(event) => setReasonDrafts((previous) => ({ ...previous, [booking.id]: event.target.value }))}
                                    rows={3}
                                    className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-rose-400"
                                    placeholder="Rejection reason"
                                  />
                                )}
                              </div>
                            ) : (
                              <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-3 py-3 text-xs text-slate-500">
                                Status locked for this stage. Open the booking or report editor for the next step.
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </ProtectedPage>
  );
}

function MetricCard({
  title,
  value,
  description,
  tone,
  icon,
}: {
  title: string;
  value: number | string;
  description: string;
  tone: keyof typeof METRIC_TONES;
  icon: React.ComponentProps<typeof AppIcon>['name'];
}) {
  return (
    <div className={`rounded-[1.75rem] border p-6 shadow-sm ${METRIC_TONES[tone]}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold">{title}</p>
          <p className="mt-3 text-3xl font-extrabold tracking-tight">{value}</p>
          <p className="mt-2 text-sm opacity-80">{description}</p>
        </div>
        <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-white/80 shadow-sm">
          <AppIcon name={icon} className="h-5 w-5" />
        </span>
      </div>
    </div>
  );
}

function getStatusButtonClass(status: string) {
  switch (status) {
    case 'SAMPLE_COLLECTED':
      return 'bg-cyan-600 hover:bg-cyan-700';
    case 'PROCESSING':
      return 'bg-amber-600 hover:bg-amber-700';
    case 'REJECTED_SAMPLE':
      return 'bg-rose-600 hover:bg-rose-700';
    default:
      return 'bg-slate-900 hover:bg-slate-800';
  }
}
