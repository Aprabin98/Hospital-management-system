import React from 'react';

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
      <p className="text-base font-semibold text-gray-800">{title}</p>
      {description ? <p className="mt-1 text-sm text-gray-600">{description}</p> : null}
      {action ? <div className="mt-3">{action}</div> : null}
    </div>
  );
}