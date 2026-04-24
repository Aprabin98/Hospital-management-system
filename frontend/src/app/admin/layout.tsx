'use client';

import type { ReactNode } from 'react';
import { usePathname } from 'next/navigation';
import { RouteGuard } from '@/components/Auth';
import { ACCESS_MATRIX, ROUTE_ACCESS } from '@/lib/access';

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname() || '/admin';
  const allowedRoles = ROUTE_ACCESS[pathname] || ACCESS_MATRIX.admin;

  return (
    <RouteGuard
      allowedRoles={allowedRoles}
      title="admin workspace"
      descriptionText="Administrative routes are restricted to administrators."
    >
      {children}
    </RouteGuard>
  );
}
