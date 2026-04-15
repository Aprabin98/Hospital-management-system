'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface Specialization {
  id: number;
  name: string;
  description?: string;
  icon?: string;
}

interface DoctorUser {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
}

interface Doctor {
  id: number;
  user: DoctorUser;
  specialization: Specialization | null;
  consultation_fee: number;
  bio?: string;
  experience_years: number;
  is_available: boolean;
  photo?: string;
  phone?: string;
}

const getErrorMessage = (err: unknown, fallback: string) => {
  if (err instanceof Error && err.message) {
    return err.message;
  }
  return fallback;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const BACKEND_ORIGIN = API_BASE_URL.replace(/\/api\/?$/, '');

export default function DoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [specializationFilter, setSpecializationFilter] = useState('');
  const [imageErrorIds, setImageErrorIds] = useState<Set<number>>(new Set());

  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    fetchDoctors();
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
  }, []);

  const fetchDoctors = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<Doctor>>('/doctors/');
      setDoctors(response.results || []);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to load doctors'));
      toast.error('Failed to load doctors');
    } finally {
      setIsLoading(false);
    }
  };

  const specializations: Specialization[] = useMemo(
    () =>
      [
        ...new Map(
          doctors
            .filter((d) => d.specialization)
            .map((d) => [d.specialization!.id, d.specialization!])
        ).values(),
      ].sort((a, b) => a.name.localeCompare(b.name)),
    [doctors]
  );

  const getDoctorName = (doctor: Doctor) => {
    const { first_name, last_name, username } = doctor.user;
    if (first_name || last_name) return `${first_name} ${last_name}`.trim();
    return username;
  };

  const getDoctorPhotoUrl = (photo?: string) => {
    if (!photo) return null;
    if (photo.startsWith('http://') || photo.startsWith('https://')) {
      return photo;
    }
    return `${BACKEND_ORIGIN}${photo.startsWith('/') ? '' : '/'}${photo}`;
  };

  const filteredDoctors = useMemo(() => {
    const normalizedTerm = searchTerm.trim().toLowerCase();

    return doctors.filter((doctor) => {
      const specializationMatches =
        !specializationFilter || String(doctor.specialization?.id || '') === specializationFilter;

      if (!specializationMatches) {
        return false;
      }

      if (!normalizedTerm) {
        return true;
      }

      const fullName = `${doctor.user.first_name || ''} ${doctor.user.last_name || ''}`.trim().toLowerCase();
      const username = (doctor.user.username || '').toLowerCase();
      const email = (doctor.user.email || '').toLowerCase();
      const phone = (doctor.phone || '').toLowerCase();
      const specializationName = (doctor.specialization?.name || '').toLowerCase();

      return (
        fullName.includes(normalizedTerm) ||
        username.includes(normalizedTerm) ||
        email.includes(normalizedTerm) ||
        phone.includes(normalizedTerm) ||
        specializationName.includes(normalizedTerm)
      );
    });
  }, [doctors, searchTerm, specializationFilter]);

  return (
    <MainLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Doctors</h1>
          <p className="mt-2 text-gray-600">View available doctors and their specializations</p>
        </div>

        {isAdmin && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800">
            <p className="font-semibold">Admin Action</p>
            <p className="mt-1">Use doctor creation form to register a new doctor account.</p>
            <Link
              href="/admin/doctors-management?create=1"
              className="mt-3 inline-flex rounded-lg border border-emerald-300 bg-white px-3 py-1.5 font-medium text-emerald-700 hover:bg-emerald-100"
            >
              Add Doctor
            </Link>
          </div>
        )}

        {/* Search & Filter */}
        <div className="flex gap-4">
          <input
            type="text"
            placeholder="Search by doctor name, email, phone, or specialization"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
          <select
            value={specializationFilter}
            onChange={(e) => setSpecializationFilter(e.target.value)}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          >
            <option value="" className="text-gray-900 bg-white">All Specializations</option>
            {specializations.map((spec) => (
              <option key={spec.id} value={spec.id} className="text-gray-900 bg-white">
                {spec.name}
              </option>
            ))}
          </select>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-600 text-sm">Loading doctors...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {!isLoading && filteredDoctors.length === 0 && (
          <div className="rounded-xl border border-gray-200 bg-white p-12 text-center">
            <p className="text-4xl mb-3">👨‍⚕️</p>
            <p className="text-gray-600 font-medium">No doctors found</p>
            {searchTerm && (
              <p className="text-sm text-gray-500 mt-1">Try adjusting your search</p>
            )}
          </div>
        )}

        {!isLoading && filteredDoctors.length > 0 && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredDoctors.map((doctor) => (
              <div
                key={doctor.id}
                className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* Doctor Photo */}
                {getDoctorPhotoUrl(doctor.photo) && !imageErrorIds.has(doctor.id) ? (
                  <div className="relative w-full h-48 bg-gray-100">
                    <Image
                      src={getDoctorPhotoUrl(doctor.photo)!}
                      alt={`Dr. ${getDoctorName(doctor)}`}
                      fill
                      sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                      className="object-cover"
                      onError={() => {
                        setImageErrorIds((prev) => {
                          const next = new Set(prev);
                          next.add(doctor.id);
                          return next;
                        });
                      }}
                    />
                  </div>
                ) : (
                  <div className="w-full h-24 bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center text-white text-3xl font-bold">
                      {getDoctorName(doctor).charAt(0).toUpperCase()}
                    </div>
                  </div>
                )}

                <div className="p-6">
                  <div className="mb-3">
                    <h3 className="text-lg font-bold text-gray-900">Dr. {getDoctorName(doctor)}</h3>
                    {doctor.specialization && (
                      <p className="text-sm font-medium text-blue-600 mt-1">
                        {doctor.specialization.name}
                      </p>
                    )}
                  </div>

                  {/* Experience & Fee */}
                  <div className="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="text-xs text-gray-500">Experience</p>
                      <p className="font-semibold text-gray-900">{doctor.experience_years} yrs</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">Consultation</p>
                      <p className="font-semibold text-gray-900">₹{doctor.consultation_fee}</p>
                    </div>
                  </div>

                  {/* Bio */}
                  {doctor.bio && (
                    <p className="text-sm text-gray-600 mb-4 line-clamp-2">{doctor.bio}</p>
                  )}

                  {/* Contact */}
                  {doctor.phone && (
                    <p className="text-sm text-gray-600 mb-4">📞 {doctor.phone}</p>
                  )}

                  {/* Status & Action */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-medium ${
                        doctor.is_available
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          doctor.is_available ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                      />
                      {doctor.is_available ? 'Available' : 'Unavailable'}
                    </span>
                    {doctor.is_available && (
                      <Link
                        href={`/appointments/create?doctor=${doctor.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-700"
                      >
                        Book Appointment →
                      </Link>
                    )}
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
