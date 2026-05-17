'use client';

import Link from 'next/link';
import { MainLayout } from '@/components/Layout';

const steps = [
  'Open demo appointment.',
  'Write symptoms: fever and cough for three days.',
  'Write medicine: Penicillin.',
  'Save report to patient history and complete appointment.',
  'Open patient profile and show care summary.',
  'Show AI causes, CBC/CRP/Chest X-Ray, risk, allergy warning.',
  'Show follow-up and document vault.',
];

export default function DemoFlowPage() {
  return (
    <MainLayout>
      <div className="space-y-6">
        <section className="rounded-xl border border-blue-200 bg-blue-50 p-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Defence Demo</p>
          <h1 className="mt-2 text-3xl font-bold text-gray-900">AI-Assisted Patient History Based Clinical Decision Support System</h1>
          <p className="mt-3 max-w-3xl text-gray-700">
            The AI does not replace doctor diagnosis. It supports the doctor by reviewing patient history, symptoms, allergies, and previous visits.
          </p>
        </section>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Demo Data</h2>
            <div className="mt-3 space-y-2 text-sm text-gray-700">
              <p>Doctor: demo.doctor@hms.test</p>
              <p>Password: Demo@12345</p>
              <p>Patient: Sita Shrestha</p>
              <p>Allergy: Penicillin</p>
              <p>History: Diabetes, Hypertension</p>
            </div>
          </div>
          <div className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-gray-900">Expected AI Output</h2>
            <div className="mt-3 space-y-2 text-sm text-gray-700">
              <p>Possible cause: Respiratory infection / Viral fever</p>
              <p>Tests: CBC, CRP, Chest X-Ray</p>
              <p>Risk: High when Penicillin allergy is detected</p>
              <p>Warning: Allergy warning: Penicillin</p>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-gray-900">Presentation Flow</h2>
          <ol className="mt-3 space-y-3">
            {steps.map((step, index) => (
              <li key={step} className="flex gap-3 text-sm text-gray-700">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">{index + 1}</span>
                <span className="pt-1">{step}</span>
              </li>
            ))}
          </ol>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link href="/appointments" className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white hover:bg-blue-700">Open Appointments</Link>
            <Link href="/patients" className="rounded-lg border border-gray-300 px-4 py-2 font-semibold text-gray-700 hover:bg-gray-50">Open Patients</Link>
          </div>
        </section>
      </div>
    </MainLayout>
  );
}
