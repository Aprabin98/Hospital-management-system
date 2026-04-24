'use client';

import type { ReactNode } from 'react';
import { RouteGuard } from '@/components/Auth';
import { ACCESS_MATRIX } from '@/lib/access';

export default function LabLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard
      allowedRoles={ACCESS_MATRIX.criticalLabValues}
      title="lab workspace"
      descriptionText="Lab routes are restricted to approved laboratory and clinical escalation roles."
    >
      {children}
    </RouteGuard>
  );
}
