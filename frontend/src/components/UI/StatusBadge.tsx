import React from 'react';

interface StatusBadgeProps {
  value: string;
}

const statusClass = (status: string) => {
  const normalized = status.toUpperCase();
  if (['DONE', 'COMPLETED', 'DISCHARGED', 'APPROVED', 'GIVEN', 'PAID', 'ACKNOWLEDGED'].includes(normalized)) {
    return 'bg-green-100 text-green-800 border-green-200';
  }
  if (['IN_PROGRESS', 'PROCESSING', 'PENDING', 'SAMPLE_COLLECTED', 'SCHEDULED', 'WAITING', 'CALLED', 'CONFIRMED'].includes(normalized)) {
    return 'bg-amber-100 text-amber-800 border-amber-200';
  }
  if (['REJECTED', 'REJECTED_SAMPLE', 'CANCELLED', 'FAILED', 'NOT_GIVEN', 'DENIED', 'OVERDUE'].includes(normalized)) {
    return 'bg-red-100 text-red-800 border-red-200';
  }
  return 'bg-slate-100 text-slate-700 border-slate-200';
};

export default function StatusBadge({ value }: StatusBadgeProps) {
  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${statusClass(value)}`}>{value}</span>;
}