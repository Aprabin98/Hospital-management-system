import React from 'react';

interface AppIconProps {
  name:
    | 'dashboard'
    | 'patients'
    | 'appointments'
    | 'doctors'
    | 'billing'
    | 'lab'
    | 'prescriptions'
    | 'rooms'
    | 'heart'
    | 'notifications'
    | 'reports'
    | 'settings'
    | 'users'
    | 'security'
    | 'emergency'
    | 'radiology'
    | 'pharmacy'
    | 'ipd'
    | 'analytics'
    | 'menu'
    | 'profile'
    | 'logout'
    | 'spark'
    | 'finance'
    | 'compliance';
  className?: string;
}

const paths: Record<AppIconProps['name'], React.ReactNode> = {
  dashboard: <path d="M4 13h7V4H4v9Zm9 7h7V11h-7v9ZM4 20h7v-5H4v5Zm9-11h7V4h-7v5Z" fill="currentColor" />,
  patients: <path d="M16 11a4 4 0 1 0-4-4 4 4 0 0 0 4 4ZM8 13a3 3 0 1 0-3-3 3 3 0 0 0 3 3Zm8 2c-3.33 0-10 1.67-10 5v1h20v-1c0-3.33-6.67-5-10-5Zm-8 0c-.52 0-1.02.03-1.5.08C4.57 15.43 2 16.68 2 19v2h4v-1c0-1.2.5-2.3 1.3-3.22A8.7 8.7 0 0 1 10 15.2c-.64-.13-1.31-.2-2-.2Z" fill="currentColor" />,
  appointments: <path d="M19 4h-1V2h-2v2H8V2H6v2H5a2 2 0 0 0-2 2v13a3 3 0 0 0 3 3h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2Zm0 16H6a1 1 0 0 1-1-1V10h14v10Zm0-12H5V6h14v2Zm-7 9h2v-3h3v-2h-3v-3h-2v3H9v2h3v3Z" fill="currentColor" />,
  doctors: <path d="M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2Zm-6 14h-2v-3H8v-2h3V9h2v3h3v2h-3v3Z" fill="currentColor" />,
  billing: <path d="M12 2 4 5v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V5l-8-3Zm1 15.93V19h-2v-1.07A4 4 0 0 1 8 14h2a2 2 0 1 0 2-2 4 4 0 1 1 4-4h-2a2 2 0 1 0-2 2 4 4 0 0 1 1 7.93Z" fill="currentColor" />,
  lab: <path d="M9 2v6.17L4.76 15.1A4 4 0 0 0 8.17 21h7.66a4 4 0 0 0 3.41-5.9L15 8.17V2h-2v6.7l4.54 7.44A2 2 0 0 1 15.83 19H8.17a2 2 0 0 1-1.71-2.96L11 8.7V2H9Z" fill="currentColor" />,
  prescriptions: <path d="M19 3H8a2 2 0 0 0-2 2v2H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2v-2h1a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2Zm-8 14H9v-2H7v-2h2v-2h2v2h2v2h-2v2Zm8-4h-1V9h-2V5h3v8Z" fill="currentColor" />,
  rooms: <path d="M3 11.5 12 4l9 7.5V20a2 2 0 0 1-2 2h-4v-6H9v6H5a2 2 0 0 1-2-2v-8.5Z" fill="currentColor" />,
  heart: <path d="m12 21-1.45-1.32C5.4 15.03 2 11.96 2 8.2 2 5.14 4.42 3 7.5 3A5.4 5.4 0 0 1 12 5.09 5.4 5.4 0 0 1 16.5 3C19.58 3 22 5.14 22 8.2c0 3.76-3.4 6.83-8.55 11.48L12 21Z" fill="currentColor" />,
  notifications: <path d="M12 22a2.5 2.5 0 0 0 2.45-2h-4.9A2.5 2.5 0 0 0 12 22Zm6-6V11a6 6 0 1 0-12 0v5L4 18v1h16v-1l-2-2Z" fill="currentColor" />,
  reports: <path d="M6 2h8l4 4v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm7 1.5V7h3.5L13 3.5ZM8 11h8v2H8v-2Zm0 4h8v2H8v-2Z" fill="currentColor" />,
  settings: <path d="m19.14 12.94.04-.94-.04-.94 2.03-1.58a.5.5 0 0 0 .12-.63l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.78 7.78 0 0 0-1.63-.94L14.4 2.8a.5.5 0 0 0-.49-.4h-3.82a.5.5 0 0 0-.49.4l-.36 2.53c-.57.23-1.11.54-1.62.94l-2.4-.96a.5.5 0 0 0-.6.22L2.7 8.85a.5.5 0 0 0 .12.63l2.03 1.58-.04.94.04.94L2.82 14.52a.5.5 0 0 0-.12.63l1.92 3.32a.5.5 0 0 0 .6.22l2.39-.96c.5.4 1.05.72 1.63.95l.36 2.52a.5.5 0 0 0 .49.4h3.82a.5.5 0 0 0 .49-.4l.36-2.52c.58-.23 1.12-.55 1.63-.95l2.39.96a.5.5 0 0 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.63l-2.03-1.58ZM12 15.5A3.5 3.5 0 1 1 12 8a3.5 3.5 0 0 1 0 7.5Z" fill="currentColor" />,
  users: <path d="M16 14c2.67 0 8 1.34 8 4v2H8v-2c0-2.66 5.33-4 8-4Zm-8-1a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm8-2a3 3 0 1 1 0-6 3 3 0 0 1 0 6Z" fill="currentColor" />,
  security: <path d="M12 2 4 5v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V5l-8-3Zm0 11a2 2 0 1 1 .001-3.999A2 2 0 0 1 12 13Zm3 4H9v-1a3 3 0 1 1 6 0v1Z" fill="currentColor" />,
  emergency: <path d="M19 13h-3v3h-4v-3H9V9h3V6h4v3h3v4Zm-7-9 7 3v5c0 4.4-2.99 8.52-7 9.8C7.99 20.52 5 16.4 5 12V7l7-3Z" fill="currentColor" />,
  radiology: <path d="M5 3h14a2 2 0 0 1 2 2v12h-2V5H5v14h6v2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm9 6a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 2.2A2.8 2.8 0 1 0 14 16.8 2.8 2.8 0 0 0 14 11.2Z" fill="currentColor" />,
  pharmacy: <path d="m15.5 4.5 4 4-9 9H6.5v-4l9-9ZM14 2l1.5 1.5-9 9H5v-1.5l9-9Z" fill="currentColor" />,
  ipd: <path d="M4 5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v14h-2v-2H6v2H4V5Zm2 2v8h12V7H6Zm4 1h2v2h2v2h-2v2h-2v-2H8v-2h2V8Z" fill="currentColor" />,
  analytics: <path d="M5 9h3v10H5V9Zm5-4h3v14h-3V5Zm5 7h3v7h-3v-7Z" fill="currentColor" />,
  menu: <path d="M4 7h16v2H4V7Zm0 5h16v2H4v-2Zm0 5h16v2H4v-2Z" fill="currentColor" />,
  profile: <path d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Zm0 2c-4.42 0-8 1.79-8 4v2h16v-2c0-2.21-3.58-4-8-4Z" fill="currentColor" />,
  logout: <path d="M10 17v-2h4V9h-4V7h4a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-4Zm-1-1-4-4 4-4v3h8v2H9v3Z" fill="currentColor" />,
  spark: <path d="m11 21 1-7 5-2-5-2-1-7-1 7-5 2 5 2 1 7Zm8-5 1.2-3L23 12l-2.8-1L19 8l-1.2 3L15 12l2.8 1L19 16ZM5 8l.8-2L8 5l-2.2-.8L5 2l-.8 2.2L2 5l2.2 1L5 8Z" fill="currentColor" />,
  finance: <path d="M4 5h16v2H4V5Zm2 4h12a2 2 0 0 1 2 2v6a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-6a2 2 0 0 1 2-2Zm4 3v5h2v-1h2a2 2 0 0 0 0-4h-4Zm2 2h2a.5.5 0 0 1 0 1h-2v-1Z" fill="currentColor" />,
  compliance: <path d="M12 2 5 5v6c0 4.62 3.13 8.94 7 10 3.87-1.06 7-5.38 7-10V5l-7-3Zm-1 13-3-3 1.4-1.4 1.6 1.58 3.6-3.58L16 10l-5 5Z" fill="currentColor" />,
};

export function AppIcon({ name, className = 'h-5 w-5' }: AppIconProps) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className}>
      {paths[name]}
    </svg>
  );
}
