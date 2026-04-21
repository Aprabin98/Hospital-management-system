'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks';
import { apiClient } from '@/lib/api';

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

  const fetchUnreadCount = async (): Promise<number> => {
    const data = await apiClient.get<{ unread_count: number }>('/notifications/unread-count/');
    return Number(data.unread_count || 0);
  };

  React.useEffect(() => {
    const loadUnread = async () => {
      try {
        const response = await fetchUnreadCount();
        setUnreadCount(response);
      } catch {
        setUnreadCount(0);
      }
    };

    if (isAuthenticated) {
      loadUnread();
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
      'bg-blue-500',
      'bg-purple-500',
      'bg-pink-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-red-500',
      'bg-indigo-500',
      'bg-cyan-500',
    ];
    if (user?.email) {
      const hash = user.email.charCodeAt(0);
      return colors[hash % colors.length];
    }
    return 'bg-blue-500';
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <header className="flex items-center justify-between border-b border-gray-300 bg-white px-6 py-4 shadow-sm">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="rounded-lg hover:bg-gray-100 p-2 transition-colors"
          title="Toggle Sidebar"
        >
          ☰
        </button>
        <h2 className="text-lg font-semibold text-gray-800">Hospital Management System</h2>
      </div>

      {isAuthenticated && user && (
        <div className="relative">
          <div className="flex items-center gap-2">
            <button
              onClick={() => router.push('/notifications')}
              className="relative rounded-lg p-2 hover:bg-gray-100 transition-colors"
              title="Notifications"
            >
              <span className="text-lg">🔔</span>
              {unreadCount > 0 && (
                <span className="absolute -right-1 -top-1 rounded-full bg-red-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </button>

            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center gap-2 rounded-lg px-3 py-2 hover:bg-gray-100 transition-colors"
            >
            <div className={`w-8 h-8 rounded-full ${getAvatarBgColor()} flex items-center justify-center text-white font-bold text-sm`}>
              {getAvatarLetter()}
            </div>
            <span className="text-sm font-medium text-gray-700">
              {user.first_name || user.email.split('@')[0]}
            </span>
            </button>
          </div>

          {isUserMenuOpen && (
            <div className="absolute right-0 mt-2 w-56 rounded-lg border border-gray-200 bg-white shadow-lg z-50">
              <div className="px-4 py-3 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full ${getAvatarBgColor()} flex items-center justify-center text-white font-bold`}>
                    {getAvatarLetter()}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {user.first_name && user.last_name
                        ? `${user.first_name} ${user.last_name}`
                        : user.first_name || user.email}
                    </p>
                    <p className="text-xs text-gray-500">{user.role}</p>
                  </div>
                </div>
              </div>
              <button
                onClick={() => router.push('/dashboard')}
                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => router.push('/profile')}
                className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
              >
                👤 Profile & Account
              </button>
              <button
                onClick={handleLogout}
                className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-gray-100 border-t border-gray-200 rounded-b-lg"
              >
                🚪 Logout
              </button>
            </div>
          )}
        </div>
      )}
    </header>
  );
}
