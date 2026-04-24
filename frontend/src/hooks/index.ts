import { useState, useCallback, useEffect } from 'react';
import { apiClient, ApiError } from '@/lib/api';
import { AuthResponse } from '@/types';
import {
  clearStoredAuthState,
  getStoredAuthState,
  hasAllowedRole,
  normalizeRole,
  onAuthStateChange,
  setStoredAuthState,
} from '@/lib/auth';

interface UseApiOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  immediate?: boolean;
}

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
}

export function useApi<T>(
  url: string,
  options: UseApiOptions = {}
): UseApiState<T> & { refetch: () => Promise<void> } {
  const { method = 'GET', immediate = true } = options;
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const fetchData = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.get<T>(url);
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({ data: null, loading: false, error: error as ApiError });
    }
  }, [url]);

  useEffect(() => {
    if (immediate && method === 'GET') {
      fetchData();
    }
  }, [url, immediate, method, fetchData]);

  return {
    ...state,
    refetch: fetchData,
  };
}

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [user, setUser] = useState<AuthResponse['user'] | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const syncAuthState = () => {
      const state = getStoredAuthState();
      setIsAuthenticated(!!state.token);
      setUserRole(state.userRole);
      setUser(state.user);
      setIsLoading(false);
    };

    syncAuthState();
    return onAuthStateChange(syncAuthState);
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<AuthResponse> => {
    try {
      const response = await apiClient.post<AuthResponse>('/auth/login/', { email, password });
      setStoredAuthState({
        token: response.token,
        refreshToken: response.refresh || null,
        role: response.role,
        user: response.user,
      });
      setIsAuthenticated(true);
      setUserRole(normalizeRole(response.role));
      setUser(response.user);
      return response;
    } catch (error) {
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout/');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearStoredAuthState();
      setIsAuthenticated(false);
      setUserRole(null);
      setUser(null);
    }
  }, []);

  return {
    isAuthenticated,
    userRole,
    user,
    isLoading,
    login,
    logout,
  };
}

export function useRoleAccess(allowedRoles: readonly string[]) {
  const auth = useAuth();

  return {
    ...auth,
    canAccess: auth.isAuthenticated && hasAllowedRole(auth.userRole, allowedRoles),
  };
}

export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(initialValue);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const item = window.localStorage.getItem(key);
      if (item) {
        try {
          setStoredValue(JSON.parse(item));
        } catch (error) {
          console.error(`Error reading localStorage key "${key}":`, error);
        }
      }
    }
  }, [key]);

  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
        }
      } catch (error) {
        console.error(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  return [storedValue, setValue] as const;
}
