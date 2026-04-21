import React from 'react';

type StatTone = 'slate' | 'blue' | 'green' | 'amber' | 'red' | 'violet';

interface StatCardProps {
  label: string;
  value: string | number;
  tone?: StatTone;
}

const toneClasses: Record<StatTone, string> = {
  slate: 'border-slate-200 bg-slate-50 text-slate-900',
  blue: 'border-blue-200 bg-blue-50 text-blue-900',
  green: 'border-green-200 bg-green-50 text-green-900',
  amber: 'border-amber-200 bg-amber-50 text-amber-900',
  red: 'border-red-200 bg-red-50 text-red-900',
  violet: 'border-violet-200 bg-violet-50 text-violet-900',
};

export default function StatCard({ label, value, tone = 'slate' }: StatCardProps) {
  return (
    <div className={`rounded-lg border p-4 ${toneClasses[tone]}`}>
      <p className="text-xs font-medium uppercase tracking-wide opacity-80">{label}</p>
      <p className="mt-1 text-3xl font-bold">{value}</p>
    </div>
  );
}