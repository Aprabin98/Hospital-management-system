'use client';

import React, { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import toast from 'react-hot-toast';
import { ProtectedPage } from '@/components/Auth';
import { useRoleAccess } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';
import { EmptyState, PageHeader, SectionCard, StatusBadge } from '@/components/UI';

interface ImagingOrder {
  id: number;
  patient_name: string;
  catalog_name: string;
  modality: string;
  priority: string;
  status: string;
  clinical_notes: string;
  created_at: string;
}

interface ImagingReport {
  id: number;
  findings: string;
  impression: string;
  recommendation: string;
  report_status: 'DRAFT' | 'FINAL';
  is_critical: boolean;
  critical_notified_at: string | null;
  updated_at: string;
}

interface ImagingAttachment {
  id: number;
  file_url: string;
  file_name: string;
  mime_type: string;
  size_bytes: number;
  metadata_json: string;
  uploaded_by_name?: string;
  created_at: string;
}

export default function RadiologyStudyDetailPage() {
  const params = useParams<{ id: string }>();
  const orderId = Number(params?.id);

  const [isLoading, setIsLoading] = useState(true);
  const [isSavingReport, setIsSavingReport] = useState(false);
  const [isReleasing, setIsReleasing] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const [order, setOrder] = useState<ImagingOrder | null>(null);
  const [report, setReport] = useState<ImagingReport | null>(null);
  const [attachments, setAttachments] = useState<ImagingAttachment[]>([]);

  const [status, setStatus] = useState('IN_PROGRESS');
  const [reportForm, setReportForm] = useState({
    findings: '',
    impression: '',
    recommendation: '',
    report_status: 'DRAFT' as 'DRAFT' | 'FINAL',
    is_critical: false,
  });
  const [attachmentForm, setAttachmentForm] = useState({
    file_url: '',
    file_name: '',
    mime_type: 'application/dicom',
    size_bytes: '0',
    metadata_json: '{"series":"1","slice_count":0}',
  });

  const { canAccess } = useRoleAccess(ACCESS_MATRIX.radiology);

  const loadStudy = useCallback(async () => {
    if (!orderId) return;

    try {
      setIsLoading(true);
      const [orderData, reportData, attachmentsData] = await Promise.all([
        apiClient.get<ImagingOrder>(`/radiology/orders/${orderId}/`),
        apiClient.get<ImagingReport>(`/radiology/orders/${orderId}/report/`),
        apiClient.get<ImagingAttachment[]>(`/radiology/orders/${orderId}/attachments/`),
      ]);

      setOrder(orderData);
      setStatus(orderData.status || 'IN_PROGRESS');
      setReport(reportData);
      setReportForm({
        findings: reportData.findings || '',
        impression: reportData.impression || '',
        recommendation: reportData.recommendation || '',
        report_status: reportData.report_status || 'DRAFT',
        is_critical: Boolean(reportData.is_critical),
      });
      setAttachments(attachmentsData || []);
    } catch (error: any) {
      toast.error(error?.message || 'Failed to load imaging study');
    } finally {
      setIsLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    if (!canAccess || !orderId) return;
    void loadStudy();
  }, [canAccess, orderId, loadStudy]);

  const updateOrderStatus = async () => {
    try {
      await apiClient.patch(`/radiology/orders/${orderId}/`, { status });
      toast.success('Imaging study status updated');
      await loadStudy();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to update study status');
    }
  };

  const submitReport = async (e: FormEvent) => {
    e.preventDefault();
    try {
      setIsSavingReport(true);
      await apiClient.put(`/radiology/orders/${orderId}/report/`, reportForm);
      toast.success('Report saved');
      await loadStudy();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to save report');
    } finally {
      setIsSavingReport(false);
    }
  };

  const releaseReport = async () => {
    try {
      setIsReleasing(true);
      await apiClient.post(`/radiology/orders/${orderId}/release/`, {});
      toast.success('Report released to patient history');
      await loadStudy();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to release report');
    } finally {
      setIsReleasing(false);
    }
  };

  const submitAttachment = async (e: FormEvent) => {
    e.preventDefault();

    if (!attachmentForm.file_url.trim() || !attachmentForm.file_name.trim()) {
      toast.error('Attachment URL and name are required');
      return;
    }

    try {
      setIsUploading(true);
      await apiClient.post(`/radiology/orders/${orderId}/attachments/`, {
        file_url: attachmentForm.file_url.trim(),
        file_name: attachmentForm.file_name.trim(),
        mime_type: attachmentForm.mime_type.trim(),
        size_bytes: Number(attachmentForm.size_bytes || 0),
        metadata_json: attachmentForm.metadata_json.trim(),
      });
      toast.success('Attachment metadata saved');
      setAttachmentForm({
        file_url: '',
        file_name: '',
        mime_type: 'application/dicom',
        size_bytes: '0',
        metadata_json: '{"series":"1","slice_count":0}',
      });
      await loadStudy();
    } catch (error: any) {
      toast.error(error?.message || 'Failed to save attachment');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <ProtectedPage
      allowedRoles={ACCESS_MATRIX.radiology}
      title="radiology study"
      description="Radiology study access is restricted to approved imaging roles."
    >
      <div className="space-y-6">
        <PageHeader
          title={order ? `Imaging Study IMG-${order.id}` : 'Imaging Study'}
          description={order ? `${order.patient_name} · ${order.catalog_name} (${order.modality})` : 'Imaging study details'}
          actions={
            <Link href="/radiology" className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800">
              Back to Radiology
            </Link>
          }
        />

        {isLoading ? (
          <SectionCard title="Loading" subtitle="Fetching study details...">
            <div className="p-6 text-sm text-gray-500">Please wait...</div>
          </SectionCard>
        ) : !order ? (
          <EmptyState title="Study not found" description="The requested imaging order was not found." />
        ) : (
          <>
            <SectionCard title="Study Workflow" subtitle="Move this study through acquisition and reporting.">
              <div className="flex flex-wrap items-center gap-3">
                <StatusBadge value={order.status} />
                <StatusBadge value={order.priority} />
                <select
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                >
                  <option value="ORDERED">Ordered</option>
                  <option value="SCHEDULED">Scheduled</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="REPORTED">Reported</option>
                  <option value="RELEASED">Released</option>
                  <option value="CANCELLED">Cancelled</option>
                </select>
                <button
                  type="button"
                  onClick={updateOrderStatus}
                  className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700"
                >
                  Update Status
                </button>
                <button
                  type="button"
                  onClick={releaseReport}
                  disabled={isReleasing}
                  className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
                >
                  {isReleasing ? 'Releasing...' : 'Release to Patient'}
                </button>
              </div>
              {order.clinical_notes ? <p className="mt-3 text-sm text-gray-700">Notes: {order.clinical_notes}</p> : null}
            </SectionCard>

            <SectionCard title="Radiology Report" subtitle="Record findings, impression, and critical flag.">
              <form className="grid gap-4" onSubmit={submitReport}>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Findings</label>
                  <textarea
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    rows={4}
                    value={reportForm.findings}
                    onChange={(e) => setReportForm((prev) => ({ ...prev, findings: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Impression</label>
                  <textarea
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    rows={3}
                    value={reportForm.impression}
                    onChange={(e) => setReportForm((prev) => ({ ...prev, impression: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Recommendation</label>
                  <textarea
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    rows={3}
                    value={reportForm.recommendation}
                    onChange={(e) => setReportForm((prev) => ({ ...prev, recommendation: e.target.value }))}
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-sm font-medium text-gray-700">Report status</label>
                    <select
                      className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      value={reportForm.report_status}
                      onChange={(e) => setReportForm((prev) => ({ ...prev, report_status: e.target.value as 'DRAFT' | 'FINAL' }))}
                    >
                      <option value="DRAFT">Draft</option>
                      <option value="FINAL">Final</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-2 pt-7">
                    <input
                      id="critical-flag"
                      type="checkbox"
                      checked={reportForm.is_critical}
                      onChange={(e) => setReportForm((prev) => ({ ...prev, is_critical: e.target.checked }))}
                    />
                    <label htmlFor="critical-flag" className="text-sm font-medium text-gray-700">
                      Mark as critical finding
                    </label>
                  </div>
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={isSavingReport}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
                  >
                    {isSavingReport ? 'Saving...' : 'Save Report'}
                  </button>
                </div>
              </form>

              {report ? (
                <p className="mt-3 text-xs text-gray-500">
                  Last updated {new Date(report.updated_at).toLocaleString()} {report.critical_notified_at ? '· Critical alert sent' : ''}
                </p>
              ) : null}
            </SectionCard>

            <SectionCard title="Attachment Metadata" subtitle="Store DICOM/image references and metadata for this study.">
              <form className="grid gap-4 md:grid-cols-2" onSubmit={submitAttachment}>
                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700">File URL</label>
                  <input
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={attachmentForm.file_url}
                    onChange={(e) => setAttachmentForm((prev) => ({ ...prev, file_url: e.target.value }))}
                    placeholder="https://storage.example.com/study.dcm"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">File name</label>
                  <input
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={attachmentForm.file_name}
                    onChange={(e) => setAttachmentForm((prev) => ({ ...prev, file_name: e.target.value }))}
                    placeholder="study-001.dcm"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">MIME type</label>
                  <input
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={attachmentForm.mime_type}
                    onChange={(e) => setAttachmentForm((prev) => ({ ...prev, mime_type: e.target.value }))}
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Size (bytes)</label>
                  <input
                    type="number"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    value={attachmentForm.size_bytes}
                    onChange={(e) => setAttachmentForm((prev) => ({ ...prev, size_bytes: e.target.value }))}
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="mb-1 block text-sm font-medium text-gray-700">Metadata JSON</label>
                  <textarea
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                    rows={3}
                    value={attachmentForm.metadata_json}
                    onChange={(e) => setAttachmentForm((prev) => ({ ...prev, metadata_json: e.target.value }))}
                  />
                </div>

                <div className="md:col-span-2">
                  <button
                    type="submit"
                    disabled={isUploading}
                    className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
                  >
                    {isUploading ? 'Saving...' : 'Save Attachment Metadata'}
                  </button>
                </div>
              </form>

              <div className="mt-4 divide-y divide-gray-100 rounded-lg border border-gray-200">
                {attachments.length === 0 ? (
                  <p className="p-4 text-sm text-gray-500">No attachments saved yet.</p>
                ) : (
                  attachments.map((attachment) => (
                    <div key={attachment.id} className="p-3 text-sm text-gray-700">
                      <p className="font-semibold">{attachment.file_name}</p>
                      <p className="text-xs text-gray-500">{attachment.mime_type} · {attachment.size_bytes} bytes</p>
                      <a href={attachment.file_url} target="_blank" rel="noreferrer" className="text-xs font-medium text-blue-700 hover:underline">
                        Open attachment URL
                      </a>
                    </div>
                  ))
                )}
              </div>
            </SectionCard>
          </>
        )}
      </div>
    </ProtectedPage>
  );
}
