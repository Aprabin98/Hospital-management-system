'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { EmptyState } from '@/components/UI';
import { useAuth } from '@/hooks';
import { getRoleLabel, hasAllowedRole } from '@/lib/auth';

interface ProtectedPageProps {
  allowedRoles: readonly string[];
  title?: string;
  description?: string;
  children: ReactNode;
  contentClassName?: string;
}

export default function ProtectedPage({
  allowedRoles,
  title = 'this workspace',
  description,
  children,
  contentClassName = 'space-y-6 p-6',
}: ProtectedPageProps) {
  const { isAuthenticated, isLoading, userRole } = useAuth();

  if (isLoading) {
    return (
      <MainLayout>
        <div className={contentClassName}>
          <EmptyState
            title={`Loading ${title}`}
            description="Checking your session and role access."
          />
        </div>
      </MainLayout>
    );
  }

  if (!isAuthenticated) {
    return (
      <MainLayout>
        <div className={contentClassName} />
      </MainLayout>
    );
  }

  if (!hasAllowedRole(userRole, allowedRoles)) {
    const allowed = allowedRoles.map(getRoleLabel).join(', ');

    return (
      <MainLayout>
        <div className={contentClassName}>
          <EmptyState
            title="Access denied"
            description={
              description ||
              `${title} is available only to: ${allowed}.`
            }
            action={
              <Link
                href="/dashboard"
                className="inline-flex rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
              >
                Back to Dashboard
              </Link>
            }
          />
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className={contentClassName}>{children}</div>
    </MainLayout>
  );
}
