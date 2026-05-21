import type { AuthResponse } from '@/types';

export const AUTH_STORAGE_KEYS = {
  accessToken: 'authToken',
  legacyAccessToken: 'token',
  refreshToken: 'refreshToken',
  userRole: 'userRole',
  user: 'user',
} as const;

const AUTH_EVENT = 'auth-state-changed';

export interface StoredAuthState {
  token: string | null;
  refreshToken: string | null;
  userRole: string | null;
  user: AuthResponse['user'] | null;
}

export function normalizeRole(role?: string | null) {
  const normalized = (role || '')
    .trim()
    .toUpperCase()
    .replace(/[\s-]+/g, '_');
  return normalized === 'LAB_ASSISTANT' ? 'LAB_TECHNICIAN' : normalized;
}

export function getStoredAuthState(): StoredAuthState {
  if (typeof window === 'undefined') {
    return { token: null, refreshToken: null, userRole: null, user: null };
  }

  const token =
    localStorage.getItem(AUTH_STORAGE_KEYS.accessToken) ||
    localStorage.getItem(AUTH_STORAGE_KEYS.legacyAccessToken);
  const refreshToken = localStorage.getItem(AUTH_STORAGE_KEYS.refreshToken);
  const userRole = normalizeRole(localStorage.getItem(AUTH_STORAGE_KEYS.userRole));
  const rawUser = localStorage.getItem(AUTH_STORAGE_KEYS.user);

  let user: AuthResponse['user'] | null = null;
  if (rawUser) {
    try {
      user = JSON.parse(rawUser) as AuthResponse['user'];
    } catch {
      user = null;
    }
  }

  return {
    token,
    refreshToken,
    userRole: userRole || null,
    user,
  };
}

function emitAuthChange() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(AUTH_EVENT));
  }
}

export function onAuthStateChange(listener: () => void) {
  if (typeof window === 'undefined') {
    return () => undefined;
  }

  const handleStorage = (event: StorageEvent) => {
    if (
      !event.key ||
      Object.values(AUTH_STORAGE_KEYS).includes(
        event.key as (typeof AUTH_STORAGE_KEYS)[keyof typeof AUTH_STORAGE_KEYS]
      )
    ) {
      listener();
    }
  };

  window.addEventListener(AUTH_EVENT, listener);
  window.addEventListener('storage', handleStorage);

  return () => {
    window.removeEventListener(AUTH_EVENT, listener);
    window.removeEventListener('storage', handleStorage);
  };
}

export function setStoredAuthState(payload: {
  token: string;
  refreshToken?: string | null;
  role?: string | null;
  user?: AuthResponse['user'] | null;
}) {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.setItem(AUTH_STORAGE_KEYS.accessToken, payload.token);
  localStorage.setItem(AUTH_STORAGE_KEYS.legacyAccessToken, payload.token);

  if (payload.refreshToken) {
    localStorage.setItem(AUTH_STORAGE_KEYS.refreshToken, payload.refreshToken);
  } else {
    localStorage.removeItem(AUTH_STORAGE_KEYS.refreshToken);
  }

  if (payload.role) {
    localStorage.setItem(AUTH_STORAGE_KEYS.userRole, normalizeRole(payload.role));
  } else {
    localStorage.removeItem(AUTH_STORAGE_KEYS.userRole);
  }

  if (payload.user) {
    localStorage.setItem(AUTH_STORAGE_KEYS.user, JSON.stringify(payload.user));
  } else {
    localStorage.removeItem(AUTH_STORAGE_KEYS.user);
  }

  emitAuthChange();
}

export function clearStoredAuthState() {
  if (typeof window === 'undefined') {
    return;
  }

  Object.values(AUTH_STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
  emitAuthChange();
}

export function hasAllowedRole(userRole: string | null | undefined, allowedRoles: readonly string[]) {
  const normalizedRole = normalizeRole(userRole);
  return allowedRoles.map((role) => normalizeRole(role)).includes(normalizedRole);
}

export function getRoleLabel(role: string) {
  return normalizeRole(role).replaceAll('_', ' ');
}
