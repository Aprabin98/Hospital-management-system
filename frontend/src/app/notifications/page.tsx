'use client';

import React, { useEffect, useState } from 'react';
import { MainLayout } from '@/components/Layout';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  notification_type: string;
  action_url?: string;
  is_read: boolean;
  created_at: string;
}

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchNotifications = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<{ results: NotificationItem[] }>('/notifications/?page_size=50');
      setNotifications(response.results || []);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to load notifications');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const markRead = async (id: number) => {
    try {
      await apiClient.post(`/notifications/${id}/mark-read/`);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err: any) {
      toast.error(err?.message || 'Failed to mark as read');
    }
  };

  const markAllRead = async () => {
    try {
      await apiClient.post('/notifications/mark-all-read/');
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      toast.success('All notifications marked as read');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to mark all as read');
    }
  };

  const deleteNotification = async (id: number) => {
    try {
      await apiClient.delete(`/notifications/${id}/`);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch (err: any) {
      toast.error(err?.message || 'Failed to delete notification');
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Notifications</h1>
            <p className="mt-2 text-gray-600">Stay updated with appointments, payments, lab and system alerts</p>
          </div>
          <button
            onClick={markAllRead}
            className="rounded-lg border border-blue-300 px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50"
            disabled={unreadCount === 0}
          >
            Mark all as read
          </button>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 text-sm text-gray-700">
          Unread: <span className="font-semibold text-gray-900">{unreadCount}</span>
        </div>

        {isLoading ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">Loading notifications...</div>
        ) : notifications.length === 0 ? (
          <div className="rounded-lg border border-gray-200 bg-white p-8 text-center text-gray-600">No notifications yet.</div>
        ) : (
          <div className="space-y-3">
            {notifications.map((item) => (
              <div
                key={item.id}
                className={`rounded-lg border p-4 ${item.is_read ? 'border-gray-200 bg-white' : 'border-blue-200 bg-blue-50'}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{item.title}</p>
                    <p className="mt-1 text-sm text-gray-700">{item.message}</p>
                    <p className="mt-2 text-xs text-gray-500">
                      {item.notification_type} • {new Date(item.created_at).toLocaleString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {!item.is_read && (
                      <button
                        onClick={() => markRead(item.id)}
                        className="rounded-md border border-blue-300 px-3 py-1.5 text-xs font-medium text-blue-700 hover:bg-blue-100"
                      >
                        Mark read
                      </button>
                    )}
                    <button
                      onClick={() => deleteNotification(item.id)}
                      className="rounded-md border border-red-300 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
