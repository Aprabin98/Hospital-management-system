import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ProtectedPage } from '@/components/Auth';
import { useAuth } from '@/hooks';
import { ACCESS_MATRIX } from '@/lib/access';
import { apiClient } from '@/lib/api';

interface DashboardData {
  incident_summary: {
    total_incidents: number;
    open_incidents: number;
    overdue_incidents: number;
  };
  sla_summary: {
    total_breaches: number;
    open_breaches: number;
    escalated_breaches: number;
    overdue_breaches: number;
  };
  drill_summary: {
    total_drills: number;
    success_rate: number;
    failed_drills: number;
    last_successful_drill_at: string | null;
    next_due_drill_at: string | null;
  };
  retention_summary: {
    active_policies: number;
    policies_due_review: number;
  };
  compliance_score: number;
  recent_incidents: Array<Record<string, any>>;
  recent_breaches: Array<Record<string, any>>;
  recent_drills: Array<Record<string, any>>;
  recent_policies: Array<Record<string, any>>;
}

interface IncidentFormState {
  title: string;
  incident_type: string;
  severity: string;
  description: string;
  due_date: string;
}

interface BreachFormState {
  process_name: string;
  category: string;
  severity: string;
  expected_at: string;
  owner_role: string;
  description: string;
}

interface DrillFormState {
  drill_type: string;
  environment: string;
  runbook_version: string;
  success: boolean;
  duration_minutes: number;
  notes: string;
}

interface PolicyFormState {
  module_name: string;
  policy_name: string;
  retention_days: number;
  archive_after_days: number;
  summary: string;
}

const emptyIncident: IncidentFormState = {
  title: '',
  incident_type: 'QUALITY',
  severity: 'MEDIUM',
  description: '',
  due_date: '',
};

const emptyBreach: BreachFormState = {
  process_name: '',
  category: 'GENERAL',
  severity: 'MEDIUM',
  expected_at: '',
  owner_role: 'ADMIN',
  description: '',
};

const emptyDrill: DrillFormState = {
  drill_type: 'BACKUP',
  environment: 'Production',
  runbook_version: '',
  success: true,
  duration_minutes: 0,
  notes: '',
};

const emptyPolicy: PolicyFormState = {
  module_name: '',
  policy_name: '',
  retention_days: 365,
  archive_after_days: 0,
  summary: '',
};

function formatDate(value: string | null | undefined) {
  if (!value) return 'N/A';
  return new Date(value).toLocaleString();
}

export default function ComplianceCenter() {
  const { userRole } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [incidentForm, setIncidentForm] = useState<IncidentFormState>(emptyIncident);
  const [breachForm, setBreachForm] = useState<BreachFormState>(emptyBreach);
  const [drillForm, setDrillForm] = useState<DrillFormState>(emptyDrill);
  const [policyForm, setPolicyForm] = useState<PolicyFormState>(emptyPolicy);
  const [busyAction, setBusyAction] = useState('');

  const hasAccess = ACCESS_MATRIX.compliance.includes((userRole || 'PATIENT').toUpperCase() as (typeof ACCESS_MATRIX.compliance)[number]);

  const loadDashboard = async () => {
    setError('');
    const response = await apiClient.get<DashboardData>('/compliance/dashboard/');
    setData(response);
  };

  useEffect(() => {
    if (!hasAccess) {
      setLoading(false);
      return;
    }

    const bootstrap = async () => {
      try {
        setLoading(true);
        await loadDashboard();
      } catch (err: any) {
        setError(err?.message || 'Failed to load compliance dashboard');
      } finally {
        setLoading(false);
      }
    };

    void bootstrap();
  }, [hasAccess]);

  const callApi = async (path: string, method: 'post' | 'patch' | 'put' = 'post', payload?: unknown) => {
    if (method === 'post') return apiClient.post(path, payload);
    if (method === 'put') return apiClient.put(path, payload);
    return apiClient.patch(path, payload);
  };

  const reload = async () => {
    setLoading(true);
    try {
      await loadDashboard();
      setError('');
    } catch (err: any) {
      setError(err?.message || 'Failed to reload compliance dashboard');
    } finally {
      setLoading(false);
    }
  };

  const createIncident = async () => {
    setBusyAction('incident');
    try {
      await callApi('/compliance/incidents/', 'post', incidentForm);
      setIncidentForm(emptyIncident);
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to create incident');
    } finally {
      setBusyAction('');
    }
  };

  const createBreach = async () => {
    setBusyAction('breach');
    try {
      await callApi('/compliance/sla-breaches/', 'post', breachForm);
      setBreachForm(emptyBreach);
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to create SLA breach');
    } finally {
      setBusyAction('');
    }
  };

  const createDrill = async () => {
    setBusyAction('drill');
    try {
      await callApi('/compliance/backup-drills/', 'post', drillForm);
      setDrillForm(emptyDrill);
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to record drill');
    } finally {
      setBusyAction('');
    }
  };

  const createPolicy = async () => {
    setBusyAction('policy');
    try {
      await callApi('/compliance/retention-policies/', 'post', policyForm);
      setPolicyForm(emptyPolicy);
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to create retention policy');
    } finally {
      setBusyAction('');
    }
  };

  const resolveIncident = async (id: number) => {
    setBusyAction(`incident-${id}`);
    try {
      await callApi(`/compliance/incidents/${id}/resolve/`, 'post', {
        closure_notes: 'Resolved from compliance dashboard',
        root_cause: 'Documented during review',
        corrective_action: 'Updated workflow and monitoring',
        preventive_action: 'Added routine compliance check',
      });
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to resolve incident');
    } finally {
      setBusyAction('');
    }
  };

  const escalateBreach = async (id: number) => {
    setBusyAction(`breach-${id}`);
    try {
      await callApi(`/compliance/sla-breaches/${id}/escalate/`, 'post', {});
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to escalate breach');
    } finally {
      setBusyAction('');
    }
  };

  const resolveBreach = async (id: number) => {
    setBusyAction(`breach-resolve-${id}`);
    try {
      await callApi(`/compliance/sla-breaches/${id}/resolve/`, 'post', {
        resolution_summary: 'Breach reviewed and closed from dashboard',
      });
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to resolve breach');
    } finally {
      setBusyAction('');
    }
  };

  const verifyDrill = async (id: number) => {
    setBusyAction(`drill-${id}`);
    try {
      await callApi(`/compliance/backup-drills/${id}/verify/`, 'post', { success: true });
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to verify drill');
    } finally {
      setBusyAction('');
    }
  };

  const executePolicy = async (id: number) => {
    setBusyAction(`policy-${id}`);
    try {
      await callApi(`/compliance/retention-policies/${id}/execute/`, 'post', {});
      await reload();
    } catch (err: any) {
      setError(err?.message || 'Failed to execute retention policy');
    } finally {
      setBusyAction('');
    }
  };

  if (!hasAccess) {
    return (
      <ProtectedPage
        allowedRoles={ACCESS_MATRIX.compliance}
        title="compliance center"
        description="This area is available only to admin and quality compliance roles."
      >
        <div />
      </ProtectedPage>
    );
  }

  if (loading && !data) {
    return (
      <ProtectedPage allowedRoles={ACCESS_MATRIX.compliance} title="compliance center">
        <div className="p-8 text-center text-slate-600">Loading compliance center...</div>
      </ProtectedPage>
    );
  }

  if (error && !data) {
    return (
      <ProtectedPage allowedRoles={ACCESS_MATRIX.compliance} title="compliance center">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">{error}</div>
      </ProtectedPage>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <ProtectedPage allowedRoles={ACCESS_MATRIX.compliance} title="compliance center" contentClassName="space-y-8">
      <div className="space-y-8">
        <div className="rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(15,118,110,0.12),rgba(255,255,255,0.92)_45%,rgba(99,102,241,0.10))] p-8 shadow-[0_22px_70px_rgba(15,23,42,0.08)]">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">Quality & Compliance</p>
              <h1 className="mt-2 text-4xl font-black tracking-tight text-slate-900">Compliance Command Center</h1>
              <p className="mt-3 max-w-2xl text-slate-600">
                Manage incidents, SLA breaches, drill verification, and retention policy execution from one admin workspace.
              </p>
            </div>
            <div className="rounded-2xl bg-slate-950 px-6 py-5 text-white shadow-lg">
              <p className="text-sm uppercase tracking-[0.2em] text-slate-300">Compliance Score</p>
              <p className="mt-2 text-5xl font-black text-emerald-400">{data.compliance_score}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard title="Open Incidents" value={data.incident_summary.open_incidents} accent="bg-rose-500" />
          <MetricCard title="Overdue Incidents" value={data.incident_summary.overdue_incidents} accent="bg-amber-500" />
          <MetricCard title="Open SLA Breaches" value={data.sla_summary.open_breaches} accent="bg-indigo-500" />
          <MetricCard title="Due Retention Reviews" value={data.retention_summary.policies_due_review} accent="bg-emerald-500" />
        </div>

        {error ? <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-red-700">{error}</div> : null}

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
          <Panel title="Incident Reporting" subtitle="Capture quality, safety, and operational events.">
            <div className="grid gap-3 md:grid-cols-2">
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Title" value={incidentForm.title} onChange={(e) => setIncidentForm({ ...incidentForm, title: e.target.value })} />
              <select className="rounded-xl border border-slate-200 px-4 py-3" value={incidentForm.incident_type} onChange={(e) => setIncidentForm({ ...incidentForm, incident_type: e.target.value })}>
                <option value="QUALITY">Quality</option>
                <option value="SAFETY">Safety</option>
                <option value="SECURITY">Security</option>
                <option value="OPERATIONAL">Operational</option>
                <option value="CLINICAL">Clinical</option>
              </select>
              <select className="rounded-xl border border-slate-200 px-4 py-3" value={incidentForm.severity} onChange={(e) => setIncidentForm({ ...incidentForm, severity: e.target.value })}>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
              <input type="date" className="rounded-xl border border-slate-200 px-4 py-3" value={incidentForm.due_date} onChange={(e) => setIncidentForm({ ...incidentForm, due_date: e.target.value })} />
            </div>
            <textarea className="mt-3 w-full rounded-xl border border-slate-200 px-4 py-3" rows={4} placeholder="Incident description" value={incidentForm.description} onChange={(e) => setIncidentForm({ ...incidentForm, description: e.target.value })} />
            <button disabled={busyAction === 'incident'} onClick={createIncident} className="mt-3 rounded-xl bg-slate-900 px-5 py-3 font-semibold text-white hover:bg-slate-800 disabled:opacity-50">
              {busyAction === 'incident' ? 'Saving...' : 'Create Incident'}
            </button>
            <div className="mt-6 space-y-3">
              {data.recent_incidents.map((incident) => (
                <div key={incident.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{incident.title}</p>
                      <p className="text-sm text-slate-600">{incident.incident_type} • {incident.severity} • {incident.status}</p>
                      <p className="mt-2 text-sm text-slate-600">{incident.description}</p>
                    </div>
                    <button disabled={busyAction === `incident-${incident.id}`} onClick={() => resolveIncident(incident.id)} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50">
                      Resolve
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="SLA Monitoring" subtitle="Track service-level misses and escalation actions.">
            <div className="grid gap-3 md:grid-cols-2">
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Process name" value={breachForm.process_name} onChange={(e) => setBreachForm({ ...breachForm, process_name: e.target.value })} />
              <select className="rounded-xl border border-slate-200 px-4 py-3" value={breachForm.category} onChange={(e) => setBreachForm({ ...breachForm, category: e.target.value })}>
                <option value="GENERAL">General</option>
                <option value="APPOINTMENT">Appointment</option>
                <option value="LAB">Lab</option>
                <option value="PHARMACY">Pharmacy</option>
                <option value="BILLING">Billing</option>
                <option value="IPD">Inpatient</option>
              </select>
              <select className="rounded-xl border border-slate-200 px-4 py-3" value={breachForm.severity} onChange={(e) => setBreachForm({ ...breachForm, severity: e.target.value })}>
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
              <input type="datetime-local" className="rounded-xl border border-slate-200 px-4 py-3" value={breachForm.expected_at} onChange={(e) => setBreachForm({ ...breachForm, expected_at: e.target.value })} />
            </div>
            <textarea className="mt-3 w-full rounded-xl border border-slate-200 px-4 py-3" rows={4} placeholder="Breach description" value={breachForm.description} onChange={(e) => setBreachForm({ ...breachForm, description: e.target.value })} />
            <button disabled={busyAction === 'breach'} onClick={createBreach} className="mt-3 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
              {busyAction === 'breach' ? 'Saving...' : 'Log Breach'}
            </button>
            <div className="mt-6 space-y-3">
              {data.recent_breaches.map((breach) => (
                <div key={breach.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{breach.process_name}</p>
                      <p className="text-sm text-slate-600">{breach.category} • {breach.severity} • {breach.status}</p>
                      <p className="mt-2 text-sm text-slate-600">{breach.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <button disabled={busyAction === `breach-${breach.id}`} onClick={() => escalateBreach(breach.id)} className="rounded-xl border border-amber-300 px-4 py-2 text-sm font-semibold text-amber-700 hover:bg-amber-50 disabled:opacity-50">
                        Escalate
                      </button>
                      <button disabled={busyAction === `breach-resolve-${breach.id}`} onClick={() => resolveBreach(breach.id)} className="rounded-xl border border-emerald-300 px-4 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-50 disabled:opacity-50">
                        Resolve
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Backup / Restore Drills" subtitle="Store evidence for resilience and disaster recovery checks.">
            <div className="grid gap-3 md:grid-cols-2">
              <select className="rounded-xl border border-slate-200 px-4 py-3" value={drillForm.drill_type} onChange={(e) => setDrillForm({ ...drillForm, drill_type: e.target.value })}>
                <option value="BACKUP">Backup</option>
                <option value="RESTORE">Restore</option>
                <option value="FULL">Full Drill</option>
              </select>
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Environment" value={drillForm.environment} onChange={(e) => setDrillForm({ ...drillForm, environment: e.target.value })} />
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Runbook version" value={drillForm.runbook_version} onChange={(e) => setDrillForm({ ...drillForm, runbook_version: e.target.value })} />
              <input type="number" min={0} className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Duration minutes" value={drillForm.duration_minutes} onChange={(e) => setDrillForm({ ...drillForm, duration_minutes: Number(e.target.value) })} />
            </div>
            <textarea className="mt-3 w-full rounded-xl border border-slate-200 px-4 py-3" rows={4} placeholder="Drill notes" value={drillForm.notes} onChange={(e) => setDrillForm({ ...drillForm, notes: e.target.value })} />
            <button disabled={busyAction === 'drill'} onClick={createDrill} className="mt-3 rounded-xl bg-emerald-600 px-5 py-3 font-semibold text-white hover:bg-emerald-700 disabled:opacity-50">
              {busyAction === 'drill' ? 'Saving...' : 'Record Drill'}
            </button>
            <div className="mt-6 space-y-3">
              {data.recent_drills.map((drill) => (
                <div key={drill.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{drill.drill_type} • {drill.environment}</p>
                      <p className="text-sm text-slate-600">{drill.success ? 'Passed' : 'Failed'} • {drill.duration_minutes} min • Next due {formatDate(drill.next_due_at)}</p>
                    </div>
                    <button disabled={busyAction === `drill-${drill.id}`} onClick={() => verifyDrill(drill.id)} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50">
                      Verify
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Retention & Archival" subtitle="Execute and review policy-driven data retention.">
            <div className="grid gap-3 md:grid-cols-2">
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Module name" value={policyForm.module_name} onChange={(e) => setPolicyForm({ ...policyForm, module_name: e.target.value })} />
              <input className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Policy name" value={policyForm.policy_name} onChange={(e) => setPolicyForm({ ...policyForm, policy_name: e.target.value })} />
              <input type="number" min={1} className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Retention days" value={policyForm.retention_days} onChange={(e) => setPolicyForm({ ...policyForm, retention_days: Number(e.target.value) })} />
              <input type="number" min={0} className="rounded-xl border border-slate-200 px-4 py-3" placeholder="Archive after days" value={policyForm.archive_after_days} onChange={(e) => setPolicyForm({ ...policyForm, archive_after_days: Number(e.target.value) })} />
            </div>
            <textarea className="mt-3 w-full rounded-xl border border-slate-200 px-4 py-3" rows={4} placeholder="Policy summary" value={policyForm.summary} onChange={(e) => setPolicyForm({ ...policyForm, summary: e.target.value })} />
            <button disabled={busyAction === 'policy'} onClick={createPolicy} className="mt-3 rounded-xl bg-slate-900 px-5 py-3 font-semibold text-white hover:bg-slate-800 disabled:opacity-50">
              {busyAction === 'policy' ? 'Saving...' : 'Save Policy'}
            </button>
            <div className="mt-6 space-y-3">
              {data.recent_policies.map((policy) => (
                <div key={policy.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <p className="font-semibold text-slate-900">{policy.module_name} • {policy.policy_name}</p>
                      <p className="text-sm text-slate-600">Retention {policy.retention_days} days • Review {formatDate(policy.next_review_at)}</p>
                    </div>
                    <button disabled={busyAction === `policy-${policy.id}`} onClick={() => executePolicy(policy.id)} className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50">
                      Execute
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </ProtectedPage>
  );
}

function MetricCard({ title, value, accent }: { title: string; value: number; accent: string }) {
  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
      <div className={`h-2 ${accent}`} />
      <div className="p-5">
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <p className="mt-3 text-4xl font-black tracking-tight text-slate-900">{value}</p>
      </div>
    </div>
  );
}

function Panel({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-slate-900">{title}</h2>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
      </div>
      {children}
    </section>
  );
}
