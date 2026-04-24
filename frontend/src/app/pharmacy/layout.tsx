'use client';

import type { ReactNode } from 'react';
import { RouteGuard } from '@/components/Auth';
import { ACCESS_MATRIX } from '@/lib/access';

export default function PharmacyLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard
      allowedRoles={ACCESS_MATRIX.pharmacy}
      title="pharmacy workspace"
      descriptionText="Pharmacy routes are restricted to pharmacy-authorized roles."
    >
      {children}
    </RouteGuard>
  );
}
