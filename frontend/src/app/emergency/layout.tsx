'use client';

import type { ReactNode } from 'react';
import { RouteGuard } from '@/components/Auth';
import { ACCESS_MATRIX } from '@/lib/access';

export default function EmergencyLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard
      allowedRoles={ACCESS_MATRIX.emergency}
      title="emergency workspace"
      descriptionText="Emergency routes are restricted to emergency-facing clinical and operations roles."
    >
      {children}
    </RouteGuard>
  );
}
