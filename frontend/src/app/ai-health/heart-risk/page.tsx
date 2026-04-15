'use client';

import React, { useEffect, useState } from 'react';
import { MainLayout } from '@/components/Layout';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api';
import { PaginatedResponse } from '@/types';

interface HeartRiskAssessment {
  id: number;
  saved?: boolean;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  age: number;
  systolic_bp: number;
  diastolic_bp: number;
  total_cholesterol: number;
  fasting_blood_sugar: number;
  bmi: number;
  smoker: boolean;
  diabetic: boolean;
  family_history: boolean;
  chest_pain: boolean;
  sedentary_lifestyle: boolean;
  summary?: string;
  recommendations?: string;
  doctor_name?: string;
  created_at: string;
}

export default function HeartRiskPage() {
  const [latestAssessment, setLatestAssessment] = useState<HeartRiskAssessment | null>(null);
  const [assessments, setAssessments] = useState<HeartRiskAssessment[]>([]);
  const [activeTab, setActiveTab] = useState<'latest' | 'history'>('latest');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    age: '',
    sex: 'M',
    systolic_bp: '',
    diastolic_bp: '',
    total_cholesterol: '',
    fasting_blood_sugar: '',
    bmi: '',
    smoker: false,
    diabetic: false,
    family_history: false,
    chest_pain: false,
    sedentary_lifestyle: false,
  });

  useEffect(() => {
    fetchHeartRiskData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  const fetchHeartRiskData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      if (activeTab === 'latest') {
        try {
          const response = await apiClient.get<HeartRiskAssessment>('/heart-risk/latest/');
          setLatestAssessment(response);
        } catch {
          setLatestAssessment(null);
        }
      } else {
        try {
          const response = await apiClient.get<PaginatedResponse<HeartRiskAssessment>>('/heart-risk/');
          setAssessments(response.results || []);
        } catch {
          setAssessments([]);
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to load heart risk data');
      toast.error('Failed to load heart risk assessment data');
    } finally {
      setIsLoading(false);
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel?.toUpperCase()) {
      case 'LOW':
        return { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', badge: 'bg-green-100 text-green-800' };
      case 'MEDIUM':
        return { bg: 'bg-yellow-50', border: 'border-yellow-200', text: 'text-yellow-800', badge: 'bg-yellow-100 text-yellow-800' };
      case 'HIGH':
        return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800', badge: 'bg-red-100 text-red-800' };
      default:
        return { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-700', badge: 'bg-gray-100 text-gray-700' };
    }
  };

  const handleSubmitAssessment = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      const response = await apiClient.post<HeartRiskAssessment>('/heart-risk/assess/', {
        ...formData,
        age: Number(formData.age),
        systolic_bp: Number(formData.systolic_bp),
        diastolic_bp: Number(formData.diastolic_bp),
        total_cholesterol: Number(formData.total_cholesterol),
        fasting_blood_sugar: Number(formData.fasting_blood_sugar),
        bmi: Number(formData.bmi),
      });

      setLatestAssessment(response);
      setActiveTab('latest');
      toast.success('Heart risk assessment created successfully');
      fetchHeartRiskData();
    } catch (err: any) {
      toast.error(err?.message || 'Failed to run heart risk check');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">AI Heart Risk Assessment</h1>
            <p className="mt-2 text-gray-600">Cardiovascular risk prediction and analysis</p>
          </div>
        </div>

        <form onSubmit={handleSubmitAssessment} className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Run New Prediction</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input type="number" placeholder="Age" required value={formData.age} onChange={(e) => setFormData((p) => ({ ...p, age: e.target.value }))} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900" />
            <select value={formData.sex} onChange={(e) => setFormData((p) => ({ ...p, sex: e.target.value }))} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900">
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
            <input type="number" placeholder="BMI" step="0.1" required value={formData.bmi} onChange={(e) => setFormData((p) => ({ ...p, bmi: e.target.value }))} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900" />
            <input type="number" placeholder="Systolic BP" required value={formData.systolic_bp} onChange={(e) => setFormData((p) => ({ ...p, systolic_bp: e.target.value }))} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900" />
            <input type="number" placeholder="Diastolic BP" required value={formData.diastolic_bp} onChange={(e) => setFormData((p) => ({ ...p, diastolic_bp: e.target.value }))} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900" />
            <input type="number" placeholder="Total Cholesterol" required value={formData.total_cholesterol} onChange={(e) => setFormData((p) => ({ ...p, total_cholesterol: e.target.value }))} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900" />
            <input type="number" placeholder="Fasting Blood Sugar" required value={formData.fasting_blood_sugar} onChange={(e) => setFormData((p) => ({ ...p, fasting_blood_sugar: e.target.value }))} className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 md:col-span-2" />
            <button type="submit" disabled={isSubmitting} className="rounded-lg bg-blue-600 px-4 py-2 text-white font-semibold hover:bg-blue-700 disabled:bg-gray-400">
              {isSubmitting ? 'Checking...' : 'Run AI Check'}
            </button>
          </div>
          <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm text-gray-700">
            {[
              ['smoker', 'Smoker'],
              ['diabetic', 'Diabetic'],
              ['family_history', 'Family History'],
              ['chest_pain', 'Chest Pain'],
              ['sedentary_lifestyle', 'Sedentary Lifestyle'],
            ].map(([key, label]) => (
              <label key={key} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={Boolean(formData[key as keyof typeof formData])}
                  onChange={(e) =>
                    setFormData((p) => ({ ...p, [key]: e.target.checked }))
                  }
                />
                {label}
              </label>
            ))}
          </div>
        </form>

        {/* Tabs */}
        <div className="flex gap-4 border-b border-gray-200">
          {(['latest', 'history'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab === 'latest' ? 'Latest Assessment' : 'Assessment History'}
            </button>
          ))}
        </div>

        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-600 text-sm">Loading...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">{error}</div>
        )}

        {/* Latest Assessment */}
        {activeTab === 'latest' && !isLoading && (
          <div>
            {latestAssessment ? (
              <div className="space-y-6">
                {/* Risk Score Card */}
                {(() => {
                  const colors = getRiskColor(latestAssessment.risk_level);
                  return (
                    <div className={`rounded-xl border ${colors.border} ${colors.bg} p-8`}>
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <p className="text-sm font-medium text-gray-600">10-Year Heart Attack Risk</p>
                          <p className="text-6xl font-bold text-gray-900 mt-2">{latestAssessment.risk_score}%</p>
                        </div>
                        <div className="text-right">
                          <span className={`inline-block rounded-full px-4 py-2 text-lg font-bold ${colors.badge}`}>
                            {latestAssessment.risk_level}
                          </span>
                          <p className="text-sm text-gray-500 mt-2">Risk Level</p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-500">
                        Assessed on {new Date(latestAssessment.created_at).toLocaleDateString('en-US', {
                          year: 'numeric', month: 'long', day: 'numeric'
                        })}
                      </p>
                    </div>
                  );
                })()}

                {/* Vital Metrics */}
                <div className="rounded-xl border border-gray-200 bg-white p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Vital Metrics</h3>
                  <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
                    {[
                      { label: 'Blood Pressure', value: `${latestAssessment.systolic_bp}/${latestAssessment.diastolic_bp}`, unit: 'mmHg' },
                      { label: 'Cholesterol', value: latestAssessment.total_cholesterol, unit: 'mg/dL' },
                      { label: 'Blood Sugar', value: latestAssessment.fasting_blood_sugar, unit: 'mg/dL' },
                      { label: 'BMI', value: latestAssessment.bmi, unit: 'kg/m²' },
                    ].map((metric) => (
                      <div key={metric.label} className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{metric.label}</p>
                        <p className="text-2xl font-bold text-gray-900 mt-2">{metric.value}</p>
                        <p className="text-xs text-gray-500 mt-1">{metric.unit}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Risk Factors */}
                <div className="rounded-xl border border-gray-200 bg-white p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Risk Factors</h3>
                  <div className="grid grid-cols-2 gap-3 md:grid-cols-3">
                    {[
                      { name: 'Smoker', value: latestAssessment.smoker },
                      { name: 'Diabetic', value: latestAssessment.diabetic },
                      { name: 'Family History', value: latestAssessment.family_history },
                      { name: 'Chest Pain', value: latestAssessment.chest_pain },
                      { name: 'Sedentary Lifestyle', value: latestAssessment.sedentary_lifestyle },
                    ].map((factor) => (
                      <div
                        key={factor.name}
                        className={`flex items-center gap-2 p-3 rounded-lg ${
                          factor.value ? 'bg-red-50 border border-red-100' : 'bg-green-50 border border-green-100'
                        }`}
                      >
                        <span className={`w-2 h-2 rounded-full ${factor.value ? 'bg-red-500' : 'bg-green-500'}`} />
                        <span className="text-sm text-gray-700 font-medium">{factor.name}</span>
                        <span className={`text-xs font-bold ml-auto ${factor.value ? 'text-red-600' : 'text-green-600'}`}>
                          {factor.value ? 'Yes' : 'No'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Summary & Recommendations */}
                {latestAssessment.summary && (
                  <div className="rounded-xl border border-blue-200 bg-blue-50 p-6">
                    <h3 className="text-lg font-semibold text-blue-900 mb-2">Assessment Summary</h3>
                    <p className="text-sm text-blue-700">{latestAssessment.summary}</p>
                  </div>
                )}
                {latestAssessment.recommendations && (
                  <div className="rounded-xl border border-green-200 bg-green-50 p-6">
                    <h3 className="text-lg font-semibold text-green-900 mb-2">Recommendations</h3>
                    <p className="text-sm text-green-700">{latestAssessment.recommendations}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-xl border border-gray-200 bg-white p-12 text-center">
                <p className="text-5xl mb-4">❤️</p>
                <p className="text-gray-700 font-semibold text-lg">No heart risk assessment available</p>
                <p className="text-sm text-gray-500 mt-2">Contact your doctor to request an assessment</p>
              </div>
            )}
          </div>
        )}

        {/* History */}
        {activeTab === 'history' && !isLoading && (
          <div className="space-y-4">
            {assessments.length === 0 ? (
              <div className="rounded-xl border border-gray-200 bg-white p-12 text-center">
                <p className="text-gray-600">No assessment history found</p>
              </div>
            ) : (
              assessments.map((assessment) => {
                const colors = getRiskColor(assessment.risk_level);
                return (
                  <div key={assessment.id} className={`rounded-xl border ${colors.border} ${colors.bg} p-6`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500">Assessment Date</p>
                        <p className="text-lg font-semibold text-gray-900 mt-1">
                          {new Date(assessment.created_at).toLocaleDateString('en-US', {
                            year: 'numeric', month: 'long', day: 'numeric'
                          })}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-4xl font-bold text-gray-900">{assessment.risk_score}%</p>
                        <span className={`inline-block rounded-full px-3 py-1 text-sm font-bold mt-2 ${colors.badge}`}>
                          {assessment.risk_level}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
