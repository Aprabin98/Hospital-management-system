import { Suspense } from 'react';
import KhaltiSuccessClient from './khalti-success-client';

export default function KhaltiSuccessPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-600">Loading payment status...</div>}>
      <KhaltiSuccessClient />
    </Suspense>
  );
}
