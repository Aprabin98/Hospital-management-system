'use client';

import type { ReactNode } from 'react';
import { RouteGuard } from '@/components/Auth';
import { ACCESS_MATRIX } from '@/lib/access';

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard
      allowedRoles={ACCESS_MATRIX.audit}
      title="admin workspace"
      descriptionText="Administrative routes are restricted to administrators."
    >
      {children}
    </RouteGuard>
  );
}
