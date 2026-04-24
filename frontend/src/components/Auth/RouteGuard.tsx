'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import { EmptyState } from '@/components/UI';
import { useAuth } from '@/hooks';
import { hasAllowedRole } from '@/lib/auth';

interface RouteGuardProps {
  allowedRoles: readonly string[];
  title: string;
  descriptionText: string;
  children: ReactNode;
}

export default function RouteGuard({
  allowedRoles,
  title,
  descriptionText,
  children,
}: RouteGuardProps) {
  const { isAuthenticated, isLoading, userRole } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return children;
  }

  if (!hasAllowedRole(userRole, allowedRoles)) {
    return (
      <MainLayout>
        <div className="space-y-6 p-6">
          <EmptyState
            title={`Access denied for ${title}`}
            description={descriptionText}
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

  return children;
}
