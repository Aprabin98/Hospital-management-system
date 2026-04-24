'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks';
import { apiClient } from '@/lib/api';
import { AppIcon } from '@/components/UI/AppIcon';

interface HeaderProps {
  onToggleSidebar: () => void;
}

interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
}

export default function Header({ onToggleSidebar }: HeaderProps) {
  const router = useRouter();
  const { logout, isAuthenticated } = useAuth();
  const [isUserMenuOpen, setIsUserMenuOpen] = React.useState(false);
  const [user, setUser] = React.useState<User | null>(null);
  const [unreadCount, setUnreadCount] = React.useState(0);

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          setUser(JSON.parse(userStr));
        } catch (error) {
          console.error('Error parsing user from localStorage:', error);
        }
      }
    }
  }, []);

  React.useEffect(() => {
    const loadUnread = async () => {
      try {
        const data = await apiClient.get<{ unread_count: number }>('/notifications/unread-count/');
        setUnreadCount(Number(data.unread_count || 0));
      } catch {
        setUnreadCount(0);
      }
    };

    if (isAuthenticated) {
      void loadUnread();
    }
  }, [isAuthenticated]);

  const getAvatarLetter = () => {
    if (user?.first_name) {
      return user.first_name.charAt(0).toUpperCase();
    }
    if (user?.email) {
      return user.email.charAt(0).toUpperCase();
    }
    return 'U';
  };

  const getAvatarBgColor = () => {
    const colors = [
      'bg-teal-600',
      'bg-cyan-600',
      'bg-indigo-600',
      'bg-emerald-600',
      'bg-amber-600',
      'bg-rose-600',
    ];
    if (user?.email) {
      const hash = user.email.charCodeAt(0);
      return colors[hash % colors.length];
    }
    return 'bg-teal-600';
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <header className="border-b border-white/60 bg-white/75 px-4 py-4 shadow-[0_10px_35px_rgba(15,23,42,0.05)] backdrop-blur xl:px-6">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onToggleSidebar}
            className="rounded-2xl border border-slate-200 bg-white p-2.5 text-slate-700 transition hover:-translate-y-0.5 hover:border-teal-200 hover:text-teal-700"
            title="Toggle Sidebar"
          >
            <AppIcon name="menu" className="h-5 w-5" />
          </button>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-teal-700">Care Operations</p>
            <h2 className="text-lg font-bold text-slate-900">MediMind Hospital Management System</h2>
          </div>
        </div>

        {isAuthenticated && user && (
          <div className="relative">
            <div className="flex items-center gap-2">
              <button
                onClick={() => router.push('/notifications')}
                className="relative rounded-2xl border border-slate-200 bg-white p-2.5 text-slate-700 transition hover:-translate-y-0.5 hover:border-teal-200 hover:text-teal-700"
                title="Notifications"
              >
                <AppIcon name="notifications" className="h-5 w-5" />
                {unreadCount > 0 && (
                  <span className="absolute -right-1 -top-1 rounded-full bg-red-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </button>

              <button
                onClick={() => setIsUserMenuOpen((value) => !value)}
                className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 transition hover:-translate-y-0.5 hover:border-teal-200"
              >
                <div className={`flex h-9 w-9 items-center justify-center rounded-full ${getAvatarBgColor()} text-sm font-bold text-white`}>
                  {getAvatarLetter()}
                </div>
                <div className="hidden text-left sm:block">
                  <p className="text-sm font-semibold text-slate-800">{user.first_name || user.email.split('@')[0]}</p>
                  <p className="text-xs uppercase tracking-wide text-slate-500">{user.role}</p>
                </div>
              </button>
            </div>

            {isUserMenuOpen && (
              <div className="absolute right-0 z-50 mt-3 w-64 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_28px_60px_rgba(15,23,42,0.18)]">
                <div className="border-b border-slate-200 bg-slate-50/80 px-4 py-4">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-full ${getAvatarBgColor()} font-bold text-white`}>
                      {getAvatarLetter()}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-900">
                        {user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.first_name || user.email}
                      </p>
                      <p className="text-xs uppercase tracking-wide text-slate-500">{user.role}</p>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                >
                  <AppIcon name="dashboard" className="h-4 w-4" />
                  Dashboard
                </button>
                <button
                  onClick={() => router.push('/profile')}
                  className="flex w-full items-center gap-3 px-4 py-3 text-left text-sm text-slate-700 transition hover:bg-slate-50"
                >
                  <AppIcon name="profile" className="h-4 w-4" />
                  Profile & Account
                </button>
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-3 border-t border-slate-200 px-4 py-3 text-left text-sm text-red-600 transition hover:bg-red-50"
                >
                  <AppIcon name="logout" className="h-4 w-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
