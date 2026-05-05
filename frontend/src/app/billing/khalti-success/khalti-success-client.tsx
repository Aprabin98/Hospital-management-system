'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { verifyKhaltiPayment } from '@/lib/khalti';

export default function KhaltiSuccessClient() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'verifying' | 'success' | 'failed'>('verifying');
  const [message, setMessage] = useState('Verifying payment...');

  useEffect(() => {
    const verify = async () => {
      try {
        if (!searchParams) {
          setStatus('failed');
          setMessage('Missing payment parameters');
          return;
        }

        const pidx = searchParams.get('pidx');
        const paymentId = searchParams.get('payment_id');
        const appointmentId = searchParams.get('appointment_id');

        if (!pidx || !paymentId) {
          setStatus('failed');
          setMessage('Invalid payment data');
          return;
        }

        const result = await verifyKhaltiPayment(pidx, parseInt(paymentId, 10));

        if (result.success && result.status === 'Completed') {
          setStatus('success');
          setMessage('Payment successful!');
          const nextTarget = appointmentId || result.appointment_id;
          setTimeout(() => {
            if (nextTarget) {
              router.push(`/appointments/${nextTarget}`);
            } else {
              router.push('/billing');
            }
          }, 2000);
        } else {
          setStatus('failed');
          setMessage('Payment verification failed');
        }
      } catch (error: any) {
        setStatus('failed');
        setMessage(error?.message || 'Verification error');
      }
    };

    verify();
  }, [searchParams, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <div className="rounded-lg border border-slate-200 bg-white p-8 text-center shadow-sm">
        {status === 'verifying' && (
          <>
            <div className="mb-4 inline-block h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-purple-600"></div>
            <p className="text-slate-600">{message}</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="mb-4 text-4xl">✅</div>
            <p className="text-lg font-semibold text-green-600">{message}</p>
            <p className="mt-2 text-sm text-slate-500">Redirecting...</p>
          </>
        )}
        {status === 'failed' && (
          <>
            <div className="mb-4 text-4xl">❌</div>
            <p className="text-lg font-semibold text-red-600">{message}</p>
            <button
              onClick={() => router.back()}
              className="mt-4 rounded-lg bg-slate-200 px-4 py-2 font-semibold text-slate-800 hover:bg-slate-300"
            >
              Go Back
            </button>
          </>
        )}
      </div>
    </div>
  );
}
