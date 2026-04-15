'use client';

import React, { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface TestTemplate {
  id: number;
  name: string;
  description: string;
  preparation: string;
  price: number;
  duration_minutes: number;
  is_available: boolean;
}

interface TemplateField {
  id: number;
  template: number;
  field_name: string;
  unit: string;
  normal_min: string | null;
  normal_max: string | null;
  critical_min: string | null;
  critical_max: string | null;
  normal_text: string;
  field_type: 'NUMBER' | 'TEXT';
  is_required: boolean;
  order: number;
}

interface TemplateSchedule {
  id: number;
  template: number;
  day: 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN';
  start_time: string;
  end_time: string;
  max_bookings: number;
  is_active: boolean;
}

const DAYS: Array<TemplateSchedule['day']> = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
const DAY_LABELS: Record<TemplateSchedule['day'], string> = {
  MON: 'Monday',
  TUE: 'Tuesday',
  WED: 'Wednesday',
  THU: 'Thursday',
  FRI: 'Friday',
  SAT: 'Saturday',
  SUN: 'Sunday',
};

export default function ManageTestsPage() {
  const [tests, setTests] = useState<TestTemplate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  const [selectedTemplate, setSelectedTemplate] = useState<TestTemplate | null>(null);
  const [templateFields, setTemplateFields] = useState<TemplateField[]>([]);
  const [templateSchedules, setTemplateSchedules] = useState<TemplateSchedule[]>([]);
  const [isAdvancedLoading, setIsAdvancedLoading] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    preparation: '',
    price: 0,
    duration_minutes: 30,
    is_available: true,
  });

  const [fieldForm, setFieldForm] = useState({
    field_name: '',
    unit: '',
    normal_min: '',
    normal_max: '',
    critical_min: '',
    critical_max: '',
    normal_text: '',
    field_type: 'NUMBER' as 'NUMBER' | 'TEXT',
    is_required: false,
    order: 0,
  });

  const [scheduleForm, setScheduleForm] = useState({
    day: 'MON' as TemplateSchedule['day'],
    start_time: '09:00',
    end_time: '17:00',
    max_bookings: 20,
    is_active: true,
  });

  const pageSize = 12;
  const isAdmin = userRole === 'ADMIN';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setUserRole((localStorage.getItem('userRole') || '').toUpperCase());
    }
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setIsLoading(true);
      const response = await apiClient.get<PaginatedResponse<TestTemplate>>('/lab/templates/');
      setTests(response.results || []);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load templates');
      toast.error('Failed to load templates');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAdvancedData = async (templateId: number) => {
    try {
      setIsAdvancedLoading(true);
      const [fieldsRes, schedulesRes] = await Promise.all([
        apiClient.get<{ count: number; results: TemplateField[] }>(`/lab/templates/${templateId}/fields/`),
        apiClient.get<{ count: number; results: TemplateSchedule[] }>(`/lab/templates/${templateId}/schedules/`),
      ]);
      setTemplateFields(fieldsRes.results || []);
      setTemplateSchedules(schedulesRes.results || []);
    } catch {
      toast.error('Failed to load template fields/schedules');
      setTemplateFields([]);
      setTemplateSchedules([]);
    } finally {
      setIsAdvancedLoading(false);
    }
  };

  const filteredTests = useMemo(() => {
    const term = searchTerm.trim().toLowerCase();
    if (!term) return tests;
    return tests.filter(
      (t) =>
        t.name.toLowerCase().includes(term) ||
        t.description.toLowerCase().includes(term) ||
        t.preparation.toLowerCase().includes(term)
    );
  }, [tests, searchTerm]);

  const paginatedTests = useMemo(() => {
    const startIdx = (currentPage - 1) * pageSize;
    return filteredTests.slice(startIdx, startIdx + pageSize);
  }, [filteredTests, currentPage]);

  const totalPages = Math.ceil(filteredTests.length / pageSize);

  const resetTemplateForm = () => {
    setEditingId(null);
    setFormData({ name: '', description: '', preparation: '', price: 0, duration_minutes: 30, is_available: true });
  };

  const openAdvancedPanel = async (template: TestTemplate) => {
    setSelectedTemplate(template);
    setFieldForm({ field_name: '', unit: '', normal_min: '', normal_max: '', critical_min: '', critical_max: '', normal_text: '', field_type: 'NUMBER', is_required: false, order: 0 });
    setScheduleForm({ day: 'MON', start_time: '09:00', end_time: '17:00', max_bookings: 20, is_active: true });
    await fetchAdvancedData(template.id);
  };

  const handleSaveTemplate = async () => {
    if (!formData.name || formData.price <= 0) {
      toast.error('Please provide valid template name and price');
      return;
    }

    try {
      if (editingId) {
        await apiClient.patch(`/lab/templates/${editingId}/`, formData);
        toast.success('Template updated successfully');
      } else {
        await apiClient.post('/lab/templates/', formData);
        toast.success('Template created successfully');
      }
      setShowModal(false);
      resetTemplateForm();
      fetchTemplates();
    } catch {
      toast.error(editingId ? 'Failed to update template' : 'Failed to create template');
    }
  };

  const handleToggleAvailability = async (testId: number, currentStatus: boolean) => {
    try {
      await apiClient.patch(`/lab/templates/${testId}/`, { is_available: !currentStatus });
      setTests((prev) => prev.map((t) => (t.id === testId ? { ...t, is_available: !currentStatus } : t)));
      toast.success('Template availability updated');
    } catch {
      toast.error('Failed to update availability');
    }
  };

  const handleDeleteTemplate = async (testId: number) => {
    if (!confirm('Delete this template?')) return;
    try {
      await apiClient.delete(`/lab/templates/${testId}/`);
      setTests((prev) => prev.filter((t) => t.id !== testId));
      if (selectedTemplate?.id === testId) {
        setSelectedTemplate(null);
        setTemplateFields([]);
        setTemplateSchedules([]);
      }
      toast.success('Template deleted');
    } catch {
      toast.error('Failed to delete template');
    }
  };

  const addField = async () => {
    if (!selectedTemplate) return;
    if (!fieldForm.field_name.trim()) {
      toast.error('Field name is required');
      return;
    }

    try {
      await apiClient.post(`/lab/templates/${selectedTemplate.id}/fields/`, {
        ...fieldForm,
        normal_min: fieldForm.normal_min || null,
        normal_max: fieldForm.normal_max || null,
        critical_min: fieldForm.critical_min || null,
        critical_max: fieldForm.critical_max || null,
      });
      toast.success('Field added');
      setFieldForm({ field_name: '', unit: '', normal_min: '', normal_max: '', critical_min: '', critical_max: '', normal_text: '', field_type: 'NUMBER', is_required: false, order: 0 });
      fetchAdvancedData(selectedTemplate.id);
    } catch {
      toast.error('Failed to add field');
    }
  };

  const deleteField = async (fieldId: number) => {
    if (!selectedTemplate) return;
    try {
      await apiClient.delete(`/lab/template-fields/${fieldId}/`);
      toast.success('Field deleted');
      fetchAdvancedData(selectedTemplate.id);
    } catch {
      toast.error('Failed to delete field');
    }
  };

  const addSchedule = async () => {
    if (!selectedTemplate) return;
    try {
      await apiClient.post(`/lab/templates/${selectedTemplate.id}/schedules/`, scheduleForm);
      toast.success('Schedule added');
      fetchAdvancedData(selectedTemplate.id);
    } catch {
      toast.error('Failed to add schedule (check duplicate day/time)');
    }
  };

  const deleteSchedule = async (scheduleId: number) => {
    if (!selectedTemplate) return;
    try {
      await apiClient.delete(`/lab/template-schedules/${scheduleId}/`);
      toast.success('Schedule deleted');
      fetchAdvancedData(selectedTemplate.id);
    } catch {
      toast.error('Failed to delete schedule');
    }
  };

  if (!isAdmin) {
    return (
      <MainLayout>
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-center">
            <p className="text-lg font-semibold text-gray-700">Access Denied</p>
            <p className="text-gray-500">Only admins can manage test templates.</p>
            <Link href="/dashboard" className="mt-4 inline-block text-blue-600 hover:text-blue-800">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Manage Lab Templates</h1>
            <p className="mt-2 text-gray-600">Template CRUD + advanced field and schedule management</p>
          </div>
          <button
            onClick={() => {
              resetTemplateForm();
              setShowModal(true);
            }}
            className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
          >
            + Create Template
          </button>
        </div>

        <div className="flex gap-4 rounded-lg bg-white p-4 shadow-sm">
          <input
            type="text"
            placeholder="Search templates..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="rounded-lg border border-gray-200 bg-gray-50 px-4 py-2 text-sm text-gray-600">Templates: {filteredTests.length}</div>
        </div>

        {isLoading ? (
          <div className="rounded-lg bg-white p-8 text-center text-gray-600 shadow-sm">Loading templates...</div>
        ) : error ? (
          <div className="rounded-lg bg-red-50 p-4 text-red-700">{error}</div>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              {filteredTests.length === 0 ? (
                <div className="rounded-lg bg-gray-50 p-8 text-center text-gray-600">No templates found.</div>
              ) : (
                <div className="space-y-3">
                  {paginatedTests.map((test) => (
                    <div key={test.id} className={`rounded-lg border p-4 shadow-sm ${selectedTemplate?.id === test.id ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-white'}`}>
                      <div className="mb-3 flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-gray-900">{test.name}</h3>
                          <p className="text-sm text-gray-500">{test.duration_minutes} min • Rs. {Number(test.price).toFixed(2)}</p>
                        </div>
                        <button
                          onClick={() => handleToggleAvailability(test.id, test.is_available)}
                          className={`rounded-full px-3 py-1 text-xs font-medium ${test.is_available ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}
                        >
                          {test.is_available ? 'Available' : 'Disabled'}
                        </button>
                      </div>

                      <p className="mb-3 text-sm text-gray-600">{test.description || 'No description'}</p>

                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={() => openAdvancedPanel(test)}
                          className="rounded border border-indigo-300 bg-indigo-50 px-3 py-1 text-sm font-medium text-indigo-700 hover:bg-indigo-100"
                        >
                          Manage Fields/Schedules
                        </button>
                        <button
                          onClick={() => {
                            setEditingId(test.id);
                            setFormData({
                              name: test.name,
                              description: test.description || '',
                              preparation: test.preparation || '',
                              price: Number(test.price) || 0,
                              duration_minutes: test.duration_minutes || 30,
                              is_available: !!test.is_available,
                            });
                            setShowModal(true);
                          }}
                          className="rounded border border-blue-300 bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700 hover:bg-blue-100"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteTemplate(test.id)}
                          className="col-span-2 rounded border border-red-300 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-100"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {totalPages > 1 && (
                <div className="mt-4 flex justify-center gap-2">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`rounded px-3 py-1 text-sm ${currentPage === page ? 'bg-blue-600 text-white' : 'border border-gray-300 text-gray-700 hover:bg-gray-100'}`}
                    >
                      {page}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
              {!selectedTemplate ? (
                <div className="py-12 text-center text-gray-500">Select a template to manage fields and schedules.</div>
              ) : isAdvancedLoading ? (
                <div className="py-12 text-center text-gray-500">Loading advanced settings...</div>
              ) : (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedTemplate.name}</h2>
                    <p className="text-sm text-gray-600">Advanced controls for result-entry fields and available test windows.</p>
                  </div>

                  <div className="rounded-lg border border-gray-200 p-3">
                    <h3 className="mb-3 text-lg font-semibold text-gray-900">Template Fields ({templateFields.length})</h3>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                      <input value={fieldForm.field_name} onChange={(e) => setFieldForm({ ...fieldForm, field_name: e.target.value })} placeholder="Field name" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <select value={fieldForm.field_type} onChange={(e) => setFieldForm({ ...fieldForm, field_type: e.target.value as 'NUMBER' | 'TEXT' })} className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900">
                        <option value="NUMBER">Number</option>
                        <option value="TEXT">Text</option>
                      </select>
                      <input value={fieldForm.unit} onChange={(e) => setFieldForm({ ...fieldForm, unit: e.target.value })} placeholder="Unit (optional)" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <input value={fieldForm.normal_text} onChange={(e) => setFieldForm({ ...fieldForm, normal_text: e.target.value })} placeholder="Normal text (for TEXT type)" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <input value={fieldForm.normal_min} onChange={(e) => setFieldForm({ ...fieldForm, normal_min: e.target.value })} placeholder="Normal min" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <input value={fieldForm.normal_max} onChange={(e) => setFieldForm({ ...fieldForm, normal_max: e.target.value })} placeholder="Normal max" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <input value={fieldForm.critical_min} onChange={(e) => setFieldForm({ ...fieldForm, critical_min: e.target.value })} placeholder="Critical min" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <input value={fieldForm.critical_max} onChange={(e) => setFieldForm({ ...fieldForm, critical_max: e.target.value })} placeholder="Critical max" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                    </div>
                    <div className="mt-2 flex items-center gap-3">
                      <label className="flex items-center gap-2 text-sm text-gray-700">
                        <input type="checkbox" checked={fieldForm.is_required} onChange={(e) => setFieldForm({ ...fieldForm, is_required: e.target.checked })} />
                        Required
                      </label>
                      <input type="number" value={fieldForm.order} onChange={(e) => setFieldForm({ ...fieldForm, order: Number(e.target.value) || 0 })} placeholder="Order" className="w-24 rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <button onClick={addField} className="rounded bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700">Add Field</button>
                    </div>
                    <div className="mt-3 space-y-2">
                      {templateFields.length === 0 ? (
                        <p className="text-sm text-gray-500">No fields configured.</p>
                      ) : (
                        templateFields.map((field) => (
                          <div key={field.id} className="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-3 py-2">
                            <div>
                              <p className="text-sm font-medium text-gray-900">{field.field_name} <span className="text-xs text-gray-500">({field.field_type})</span></p>
                              <p className="text-xs text-gray-600">Range: {field.normal_min ?? '-'} to {field.normal_max ?? '-'} • Unit: {field.unit || 'n/a'}</p>
                            </div>
                            <button onClick={() => deleteField(field.id)} className="rounded border border-red-300 bg-red-50 px-2 py-1 text-xs text-red-700 hover:bg-red-100">Delete</button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  <div className="rounded-lg border border-gray-200 p-3">
                    <h3 className="mb-3 text-lg font-semibold text-gray-900">Template Schedules ({templateSchedules.length})</h3>
                    <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                      <select value={scheduleForm.day} onChange={(e) => setScheduleForm({ ...scheduleForm, day: e.target.value as TemplateSchedule['day'] })} className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900">
                        {DAYS.map((day) => (
                          <option key={day} value={day}>{DAY_LABELS[day]}</option>
                        ))}
                      </select>
                      <input type="number" value={scheduleForm.max_bookings} onChange={(e) => setScheduleForm({ ...scheduleForm, max_bookings: Number(e.target.value) || 20 })} placeholder="Max bookings" className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 placeholder:text-gray-500" />
                      <input type="time" value={scheduleForm.start_time} onChange={(e) => setScheduleForm({ ...scheduleForm, start_time: e.target.value })} className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900" />
                      <input type="time" value={scheduleForm.end_time} onChange={(e) => setScheduleForm({ ...scheduleForm, end_time: e.target.value })} className="rounded border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900" />
                    </div>
                    <div className="mt-2 flex items-center gap-3">
                      <label className="flex items-center gap-2 text-sm text-gray-700">
                        <input type="checkbox" checked={scheduleForm.is_active} onChange={(e) => setScheduleForm({ ...scheduleForm, is_active: e.target.checked })} />
                        Active
                      </label>
                      <button onClick={addSchedule} className="rounded bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700">Add Schedule</button>
                    </div>
                    <div className="mt-3 space-y-2">
                      {templateSchedules.length === 0 ? (
                        <p className="text-sm text-gray-500">No schedules configured.</p>
                      ) : (
                        templateSchedules.map((item) => (
                          <div key={item.id} className="flex items-center justify-between rounded border border-gray-200 bg-gray-50 px-3 py-2">
                            <div>
                              <p className="text-sm font-medium text-gray-900">{DAY_LABELS[item.day]} • {item.start_time} - {item.end_time}</p>
                              <p className="text-xs text-gray-600">Max bookings: {item.max_bookings} • {item.is_active ? 'Active' : 'Inactive'}</p>
                            </div>
                            <button onClick={() => deleteSchedule(item.id)} className="rounded border border-red-300 bg-red-50 px-2 py-1 text-xs text-red-700 hover:bg-red-100">Delete</button>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-lg bg-white p-6 shadow-xl">
              <h2 className="mb-4 text-2xl font-bold text-gray-900">{editingId ? 'Edit Template' : 'Create Template'}</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Template Name *</label>
                  <input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Price (Rs.) *</label>
                  <input type="number" min="0" step="0.01" value={formData.price} onChange={(e) => setFormData({ ...formData, price: Number(e.target.value) })} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Duration (minutes)</label>
                  <input type="number" min="5" step="5" value={formData.duration_minutes} onChange={(e) => setFormData({ ...formData, duration_minutes: Number(e.target.value) })} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Preparation</label>
                  <textarea value={formData.preparation} onChange={(e) => setFormData({ ...formData, preparation: e.target.value })} rows={2} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900" />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} rows={3} className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900" />
                </div>

                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input type="checkbox" checked={formData.is_available} onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })} />
                  Available for booking
                </label>
              </div>

              <div className="mt-6 flex gap-3">
                <button onClick={() => setShowModal(false)} className="flex-1 rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50">Cancel</button>
                <button onClick={handleSaveTemplate} className="flex-1 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700">{editingId ? 'Update' : 'Create'}</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
