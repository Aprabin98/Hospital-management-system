import { apiClient } from '@/lib/api';

export async function initiateKhaltiPayment(paymentId: number, returnUrl: string) {
  const response = await apiClient.post('/payments/khalti/initiate/', {
    payment_id: paymentId,
    return_url: returnUrl,
  });
  return response;
}

export async function verifyKhaltiPayment(pidx: string, paymentId: number) {
  const response = await apiClient.post('/payments/khalti/verify/', {
    pidx,
    payment_id: paymentId,
  });
  return response;
}

export function openKhaltiWindow(paymentUrl: string) {
  const width = 600;
  const height = 800;
  const left = (window.innerWidth - width) / 2;
  const top = (window.innerHeight - height) / 2;
  window.open(
    paymentUrl,
    'KhaltiPayment',
    `width=${width},height=${height},left=${left},top=${top}`
  );
}
