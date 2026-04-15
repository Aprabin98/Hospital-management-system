'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';

const BACKEND_ORIGIN = process.env.NEXT_PUBLIC_API_URL
  ? process.env.NEXT_PUBLIC_API_URL.replace(/\/api\/?$/, '')
  : 'http://localhost:8000';

interface SpecializationChoice {
  id: number;
  name: string;
}

interface DoctorProfileResponse {
  id?: number;
  specialization: number | null;
  specialization_name?: string;
  consultation_fee: string | number;
  experience_years: string | number;
  phone: string;
  bio: string;
  is_available: boolean;
  photo: string;
}

interface PatientProfileResponse {
  id?: number;
  full_name?: string;
  phone: string;
  gender: string;
  date_of_birth: string;
  blood_group: string;
  height: string | number | null;
  weight: string | number | null;
  address: string;
  emergency_contact: string;
}

interface ProfileResponse {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  doctor_profile?: DoctorProfileResponse;
  patient_profile?: PatientProfileResponse;
  specialization_choices?: SpecializationChoice[];
}

interface DoctorProfileForm {
  specialization: string;
  consultation_fee: string;
  experience_years: string;
  phone: string;
  bio: string;
  is_available: boolean;
  photo: string;
  photoFile: File | null;
}

interface PatientProfileForm {
  phone: string;
  gender: string;
  date_of_birth: string;
  blood_group: string;
  height: string;
  weight: string;
  address: string;
  emergency_contact: string;
}

export default function ProfilePage() {
  const [isDoctorMode, setIsDoctorMode] = useState(false);
  const [specializations, setSpecializations] = useState<SpecializationChoice[]>([]);
  const [profileRole, setProfileRole] = useState('');
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    username: '',
    doctor_profile: {
      specialization: '',
      consultation_fee: '',
      experience_years: '',
      phone: '',
      bio: '',
      is_available: true,
      photo: '',
      photoFile: null,
    } as DoctorProfileForm,
    patient_profile: {
      phone: '',
      gender: '',
      date_of_birth: '',
      blood_group: '',
      height: '',
      weight: '',
      address: '',
      emergency_contact: '',
    } as PatientProfileForm,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProfile();
  }, []);

  const displayName = useMemo(() => {
    if (profileRole === 'DOCTOR') {
      return `Dr. ${formData.first_name || formData.username || 'Doctor'}`;
    }

    if (formData.first_name || formData.last_name) {
      return [formData.first_name, formData.last_name].filter(Boolean).join(' ');
    }

    return formData.username || 'My Profile';
  }, [formData.first_name, formData.last_name, formData.username, profileRole]);

  const getAbsolutePhotoUrl = (photo: string) => {
    if (!photo) return '';
    if (photo.startsWith('http://') || photo.startsWith('https://')) {
      return photo;
    }
    return `${BACKEND_ORIGIN}${photo.startsWith('/') ? '' : '/'}${photo}`;
  };

  const fetchProfile = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.get<ProfileResponse>('/profile/');

      const role = String(response.role || '').toUpperCase();
      const hasDoctorProfile = !!response.doctor_profile;
      setProfileRole(role);
      setIsDoctorMode(hasDoctorProfile && role === 'DOCTOR');
      setSpecializations(response.specialization_choices || []);

      setFormData({
        first_name: response.first_name || '',
        last_name: response.last_name || '',
        username: response.username || '',
        doctor_profile: {
          specialization: response.doctor_profile?.specialization ? String(response.doctor_profile.specialization) : '',
          consultation_fee: response.doctor_profile?.consultation_fee ? String(response.doctor_profile.consultation_fee) : '',
          experience_years: response.doctor_profile?.experience_years ? String(response.doctor_profile.experience_years) : '',
          phone: response.doctor_profile?.phone || '',
          bio: response.doctor_profile?.bio || '',
          is_available: typeof response.doctor_profile?.is_available === 'boolean'
            ? response.doctor_profile.is_available
            : true,
          photo: response.doctor_profile?.photo || '',
          photoFile: null,
        },
        patient_profile: {
          phone: response.patient_profile?.phone || '',
          gender: response.patient_profile?.gender || '',
          date_of_birth: response.patient_profile?.date_of_birth || '',
          blood_group: response.patient_profile?.blood_group || '',
          height: response.patient_profile?.height != null ? String(response.patient_profile.height) : '',
          weight: response.patient_profile?.weight != null ? String(response.patient_profile.weight) : '',
          address: response.patient_profile?.address || '',
          emergency_contact: response.patient_profile?.emergency_contact || '',
        },
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load profile');
      toast.error('Failed to load profile');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePatientInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    if (name.startsWith('patient_')) {
      const fieldName = name.replace('patient_', '');
      setFormData((prev) => ({
        ...prev,
        patient_profile: {
          ...prev.patient_profile,
          [fieldName]: value,
        },
      }));
      return;
    }

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDoctorInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;

    if (name === 'username') {
      setFormData((prev) => ({ ...prev, username: value }));
      return;
    }

    if (name === 'doctor_photo' && type === 'file') {
      const fileInput = e.target as HTMLInputElement;
      const file = fileInput.files && fileInput.files[0] ? fileInput.files[0] : null;
      setFormData((prev) => ({
        ...prev,
        doctor_profile: {
          ...prev.doctor_profile,
          photoFile: file,
        },
      }));
      return;
    }

    if (name === 'doctor_is_available' && type === 'checkbox') {
      const checkboxInput = e.target as HTMLInputElement;
      setFormData((prev) => ({
        ...prev,
        doctor_profile: {
          ...prev.doctor_profile,
          is_available: checkboxInput.checked,
        },
      }));
      return;
    }

    const fieldName = name.replace('doctor_', '');
    setFormData((prev) => ({
      ...prev,
      doctor_profile: {
        ...prev.doctor_profile,
        [fieldName]: value,
      },
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSaving(true);

      if (isDoctorMode) {
        const payload = new FormData();
        payload.append('username', formData.username);
        payload.append('doctor_specialization', formData.doctor_profile.specialization);
        payload.append('doctor_consultation_fee', formData.doctor_profile.consultation_fee);
        payload.append('doctor_experience_years', formData.doctor_profile.experience_years);
        payload.append('doctor_phone', formData.doctor_profile.phone);
        payload.append('doctor_bio', formData.doctor_profile.bio);
        payload.append('doctor_is_available', String(formData.doctor_profile.is_available));

        if (formData.doctor_profile.photoFile) {
          payload.append('doctor_photo', formData.doctor_profile.photoFile);
        }

        await apiClient.patch('/profile/', payload, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      } else {
        await apiClient.put('/profile/', {
          first_name: formData.first_name,
          last_name: formData.last_name,
          patient_profile: formData.patient_profile,
        });
      }

      toast.success('Profile updated successfully');
      await fetchProfile();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex h-64 items-center justify-center">
          <div className="text-lg text-gray-600">Loading...</div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="max-w-3xl space-y-6">
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        <div className="rounded-2xl border border-slate-200 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-700 p-6 text-white shadow-sm">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-300">Profile</p>
              <h1 className="mt-2 text-3xl font-bold">{isDoctorMode ? 'Doctor Profile' : 'My Profile'}</h1>
              <p className="mt-2 max-w-2xl text-sm text-slate-300">
                {isDoctorMode
                  ? 'Manage your professional details, consultation settings, and availability.'
                  : 'Manage your personal and contact details from one place.'}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm md:min-w-80">
              <div className="rounded-xl border border-white/10 bg-white/10 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-300">Role</p>
                <p className="mt-1 font-semibold">{profileRole || 'USER'}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/10 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-300">Account</p>
                <p className="mt-1 truncate font-semibold">{formData.username || 'N/A'}</p>
              </div>
              <div className="col-span-2 rounded-xl border border-white/10 bg-white/10 p-3">
                <p className="text-xs uppercase tracking-wide text-slate-300">Display Name</p>
                <p className="mt-1 font-semibold">{displayName}</p>
              </div>
            </div>
          </div>
        </div>

        {isDoctorMode ? (
          <form onSubmit={handleSave} className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="p-6">
              <div className="mb-6 rounded-xl bg-blue-50 px-4 py-3 text-sm text-blue-800">
                Update your doctor information below. Fields marked here are what patients and staff will see.
              </div>
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Specialization</label>
                  <select
                    name="doctor_specialization"
                    value={formData.doctor_profile.specialization}
                    onChange={handleDoctorInputChange}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Select specialization</option>
                    {specializations.map((spec) => (
                      <option key={spec.id} value={String(spec.id)}>
                        {spec.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Consultation fee</label>
                  <input
                    type="number"
                    step="0.01"
                    name="doctor_consultation_fee"
                    value={formData.doctor_profile.consultation_fee}
                    onChange={handleDoctorInputChange}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Experience years</label>
                  <input
                    type="number"
                    name="doctor_experience_years"
                    value={formData.doctor_profile.experience_years}
                    onChange={handleDoctorInputChange}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Phone</label>
                  <input
                    type="text"
                    name="doctor_phone"
                    value={formData.doctor_profile.phone}
                    onChange={handleDoctorInputChange}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Bio</label>
                  <textarea
                    name="doctor_bio"
                    value={formData.doctor_profile.bio}
                    onChange={handleDoctorInputChange}
                    rows={4}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Photo</label>
                  <input
                    type="file"
                    name="doctor_photo"
                    accept="image/*"
                    onChange={handleDoctorInputChange}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 file:mr-3 file:rounded-md file:border-0 file:bg-blue-50 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-blue-700"
                  />
                  {formData.doctor_profile.photo && (
                    <a
                      href={getAbsolutePhotoUrl(formData.doctor_profile.photo)}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-sm text-blue-600 hover:text-blue-700"
                    >
                      View current photo
                    </a>
                  )}
                  {specializations.length > 0 && (
                    <p className="mt-2 text-xs text-gray-500">
                      Active specializations loaded: {specializations.length}
                    </p>
                  )}
                </div>

                <div>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Is available</label>
                  <div className="mt-2 flex items-center gap-3">
                    <input
                      type="checkbox"
                      name="doctor_is_available"
                      checked={formData.doctor_profile.is_available}
                      onChange={handleDoctorInputChange}
                      className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Accepting appointments</span>
                  </div>
                </div>

                <div>
                  <label className="mb-1 block text-sm font-semibold text-gray-700">Username</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleDoctorInputChange}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-gray-200 px-6 py-4">
              <button
                type="submit"
                disabled={isSaving}
                className="rounded-lg bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                type="button"
                onClick={fetchProfile}
                className="ml-2 rounded-lg border border-gray-300 px-5 py-2.5 font-medium text-gray-700 hover:bg-gray-100"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleSave} className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">
            <div className="border-b border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900">Personal Information</h2>
              <p className="mt-1 text-sm text-gray-600">Update your name and contact details</p>
            </div>

            <div className="space-y-6 p-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">First Name</label>
                  <input
                    type="text"
                    name="first_name"
                    value={formData.first_name}
                    onChange={handlePatientInputChange}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700">Last Name</label>
                  <input
                    type="text"
                    name="last_name"
                    value={formData.last_name}
                    onChange={handlePatientInputChange}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">Profile summary</p>
                <p className="mt-1">{displayName}</p>
                <p className="text-xs text-slate-500">Role: {profileRole || 'USER'}</p>
              </div>

              <div className="border-t border-gray-200" />

              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Phone Number</label>
                    <input
                      type="tel"
                      name="patient_phone"
                      value={formData.patient_profile.phone}
                      onChange={handlePatientInputChange}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Emergency Contact</label>
                    <input
                      type="tel"
                      name="patient_emergency_contact"
                      value={formData.patient_profile.emergency_contact}
                      onChange={handlePatientInputChange}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Gender</label>
                    <select
                      name="patient_gender"
                      value={formData.patient_profile.gender}
                      onChange={handlePatientInputChange}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    >
                      <option value="">Select Gender</option>
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Date of Birth</label>
                    <input
                      type="date"
                      name="patient_date_of_birth"
                      value={formData.patient_profile.date_of_birth}
                      onChange={handlePatientInputChange}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Blood Group</label>
                    <select
                      name="patient_blood_group"
                      value={formData.patient_profile.blood_group}
                      onChange={handlePatientInputChange}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    >
                      <option value="">Select Blood Group</option>
                      <option value="O+">O+</option>
                      <option value="O-">O-</option>
                      <option value="A+">A+</option>
                      <option value="A-">A-</option>
                      <option value="B+">B+</option>
                      <option value="B-">B-</option>
                      <option value="AB+">AB+</option>
                      <option value="AB-">AB-</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Height (cm)</label>
                    <input
                      type="number"
                      name="patient_height"
                      value={formData.patient_profile.height}
                      onChange={handlePatientInputChange}
                      className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Weight (kg)</label>
                  <input
                    type="number"
                    name="patient_weight"
                    value={formData.patient_profile.weight}
                    onChange={handlePatientInputChange}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Address</label>
                  <textarea
                    name="patient_address"
                    value={formData.patient_profile.address}
                    onChange={handlePatientInputChange}
                    rows={3}
                    className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex gap-4 border-t border-gray-200 p-6">
              <button
                type="submit"
                disabled={isSaving}
                className="rounded-lg bg-blue-600 px-6 py-2 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
              <button
                type="button"
                onClick={fetchProfile}
                className="rounded-lg bg-gray-200 px-6 py-2 font-medium text-gray-700 hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </MainLayout>
  );
}
