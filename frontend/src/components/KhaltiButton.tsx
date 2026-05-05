'use client';

import { useState } from 'react';
import { initiateKhaltiPayment, openKhaltiWindow } from '@/lib/khalti';

interface KhaltiButtonProps {
  paymentId: number;
  amount: number;
}

export default function KhaltiButton({ paymentId, amount }: KhaltiButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    setLoading(true);
    try {
      const returnUrl = `${window.location.origin}/billing/khalti-success?payment_id=${paymentId}`;
      const result = await initiateKhaltiPayment(paymentId, returnUrl);
      
      if (result.success && result.payment_url) {
        openKhaltiWindow(result.payment_url);
      } else {
        alert('Failed to initiate payment');
      }
    } catch (error) {
      alert('Error: ' + (error as any).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={loading}
      className="w-full rounded-lg bg-purple-600 px-4 py-3 font-semibold text-white hover:bg-purple-700 disabled:opacity-50"
    >
      {loading ? 'Processing...' : `Pay Rs. ${amount} with Khalti`}
    </button>
  );
}
