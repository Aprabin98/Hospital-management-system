'use client';

import type { ReactNode } from 'react';
import { RouteGuard } from '@/components/Auth';
import { ACCESS_MATRIX } from '@/lib/access';

export default function IPDLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard
      allowedRoles={ACCESS_MATRIX.ipd}
      title="IPD workspace"
      descriptionText="IPD routes are restricted to inpatient-authorized roles."
    >
      {children}
    </RouteGuard>
  );
}
