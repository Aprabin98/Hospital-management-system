type ApiLikeError = {
  message?: string;
  detail?: string;
  data?: {
    detail?: string;
    message?: string;
  };
};

export function extractApiErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (!error) return fallback;

  if (typeof error === 'string') {
    return error;
  }

  if (typeof error === 'object') {
    const err = error as ApiLikeError;
    return err.message || err.detail || err.data?.detail || err.data?.message || fallback;
  }

  return fallback;
}
