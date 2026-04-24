'use client';

import type { ReactNode } from 'react';
import { RouteGuard } from '@/components/Auth';
import { ACCESS_MATRIX } from '@/lib/access';

export default function RadiologyLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard
      allowedRoles={ACCESS_MATRIX.radiologyHistory}
      title="radiology workspace"
      descriptionText="Radiology routes are restricted to approved imaging and history access roles."
    >
      {children}
    </RouteGuard>
  );
}
