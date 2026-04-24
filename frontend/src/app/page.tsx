import Image from 'next/image';
import Link from 'next/link';

const serviceCards = [
  {
    title: 'Appointments and OPD',
    label: 'Front desk',
    description:
      'Fast appointment booking, doctor slots, queue handling, and patient flow coordination.',
  },
  {
    title: 'Laboratory and Diagnostics',
    label: 'Diagnostics',
    description:
      'Lab bookings, result release, templates, critical value tracking, and quality control logs.',
  },
  {
    title: 'Billing and Insurance',
    label: 'Finance',
    description:
      'Invoices, refunds, insurance verification, pre-authorizations, claims, and reconciliation.',
  },
  {
    title: 'Prescriptions and Pharmacy',
    label: 'Medication',
    description:
      'Digital prescriptions, dispense workflow, stock visibility, and controlled drug logs.',
  },
  {
    title: 'Inpatient and Emergency',
    label: 'Care delivery',
    description:
      'IPD stays, rounds, discharge workflow, emergency encounters, and room assignment operations.',
  },
  {
    title: 'Audit, Notifications, and AI',
    label: 'Operations',
    description:
      'Security logs, role-based access, in-app alerts, WhatsApp notifications, and AI health tools.',
  },
];

const highlights = [
  'Role-based access for admin, doctor, nurse, receptionist, lab, pharmacy, and patient users',
  'JWT authentication with refresh flow and optional 2FA verification',
  'Responsive operational workspace for hospital departments',
  'PDF receipts, lab reports, and prescriptions generated inside the system',
];

const hospitalServices = [
  'Outpatient consultation',
  'Emergency care support',
  'Laboratory testing',
  'Radiology workflow',
  'Pharmacy operations',
  'Inpatient admission and discharge',
  'Insurance and billing desk',
  'Medical records and clinical documentation',
];

const metrics = [
  { value: '20+', label: 'Hospital modules' },
  { value: '10', label: 'User roles supported' },
  { value: '24/7', label: 'Operational readiness theme' },
  { value: '1', label: 'Unified care platform' },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.16),transparent_28%),radial-gradient(circle_at_82%_12%,rgba(15,118,110,0.18),transparent_24%),linear-gradient(180deg,rgba(255,255,255,0.86),rgba(241,245,249,0.96))]" />
        <div className="relative mx-auto max-w-7xl px-4 pb-20 pt-6 sm:px-6 lg:px-8">
          <header className="rounded-full border border-white/70 bg-white/80 px-4 py-3 shadow-[0_16px_40px_rgba(15,23,42,0.08)] backdrop-blur md:px-6">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div className="flex items-center gap-3">
                <Image
                  src="/medimind-logo.svg"
                  alt="MediMind"
                  width={48}
                  height={48}
                  className="h-12 w-12 rounded-2xl"
                  priority
                />
                <div>
                  <div className="text-lg font-extrabold tracking-tight text-slate-950">MediMind</div>
                  <div className="text-sm text-slate-500">Hospital Management System</div>
                </div>
              </div>
              <nav className="flex flex-wrap items-center gap-3 text-sm font-semibold text-slate-600">
                <a href="#services" className="hover:text-slate-950">Services</a>
                <a href="#modules" className="hover:text-slate-950">Modules</a>
                <a href="#workflow" className="hover:text-slate-950">Workflow</a>
                <Link
                  href="/login"
                  className="rounded-full border border-slate-200 px-4 py-2 text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  Login
                </Link>
                <Link
                  href="/dashboard"
                  className="rounded-full bg-slate-950 px-4 py-2 text-white transition hover:bg-slate-800"
                >
                  Open Workspace
                </Link>
              </nav>
            </div>
          </header>

          <div className="grid gap-10 pt-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
            <div>
              <div className="inline-flex items-center rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-bold uppercase tracking-[0.24em] text-teal-700">
                Unified hospital operations
              </div>
              <h1 className="mt-6 max-w-3xl text-4xl font-black leading-tight tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
                Responsive hospital software for appointments, diagnostics, billing, pharmacy, and patient care.
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
                MediMind brings front desk, doctors, nurses, lab teams, pharmacy, finance, and compliance workflows
                into one modern platform built with Django and Next.js.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link
                  href="/login"
                  className="inline-flex items-center justify-center rounded-2xl bg-teal-700 px-6 py-3 text-sm font-bold text-white shadow-[0_20px_40px_rgba(15,118,110,0.24)] transition hover:bg-teal-800"
                >
                  Start Secure Login
                </Link>
                <Link
                  href="/register"
                  className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-bold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
                >
                  Create Patient Account
                </Link>
              </div>
              <div className="mt-8 grid gap-3 sm:grid-cols-2">
                {highlights.map((item) => (
                  <div key={item} className="rounded-2xl border border-slate-200/80 bg-white/85 px-4 py-4 text-sm text-slate-600 shadow-[0_12px_30px_rgba(15,23,42,0.05)]">
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="absolute -left-8 top-8 hidden h-24 w-24 rounded-full bg-cyan-200/40 blur-2xl md:block" />
              <div className="absolute -right-6 bottom-16 hidden h-28 w-28 rounded-full bg-emerald-200/40 blur-2xl md:block" />
              <div className="relative overflow-hidden rounded-[2rem] border border-white/80 bg-slate-950 p-6 text-white shadow-[0_30px_90px_rgba(15,23,42,0.24)]">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-[0.24em] text-cyan-200">Care command center</p>
                    <h2 className="mt-2 text-2xl font-extrabold">All hospital services in one system</h2>
                  </div>
                  <div className="rounded-2xl bg-white/10 p-3">
                    <Image src="/medimind-logo.svg" alt="MediMind logo" width={42} height={42} className="h-10 w-10" />
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  {metrics.map((item) => (
                    <div key={item.label} className="rounded-2xl border border-white/10 bg-white/6 p-4">
                      <div className="text-2xl font-black">{item.value}</div>
                      <div className="mt-1 text-sm text-slate-300">{item.label}</div>
                    </div>
                  ))}
                </div>

                <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-gradient-to-br from-cyan-500/20 via-slate-900 to-emerald-500/20 p-5">
                  <p className="text-sm font-semibold text-cyan-100">Hospital service gallery</p>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {hospitalServices.map((service) => (
                      <div key={service} className="rounded-2xl border border-white/10 bg-white/8 px-4 py-3 text-sm text-slate-100">
                        {service}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="services" className="mx-auto max-w-7xl px-4 py-18 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.22em] text-teal-700">Hospital services</p>
            <h2 className="mt-2 text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">
              The homepage now shows the full service story of the system.
            </h2>
          </div>
          <p className="max-w-xl text-sm leading-7 text-slate-600 sm:text-base">
            Instead of a blank redirect screen, the landing page now communicates what the hospital provides across care,
            diagnostics, operations, and administration.
          </p>
        </div>

        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {serviceCards.map((card, index) => (
            <article
              key={card.title}
              className="group rounded-[1.75rem] border border-slate-200/80 bg-white/90 p-6 shadow-[0_18px_50px_rgba(15,23,42,0.06)] transition duration-200 hover:-translate-y-1 hover:shadow-[0_26px_70px_rgba(15,23,42,0.1)]"
            >
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase tracking-[0.18em] text-slate-500">
                  {card.label}
                </span>
                <span className="text-xs font-bold text-teal-700">0{index + 1}</span>
              </div>
              <h3 className="mt-5 text-2xl font-extrabold tracking-tight text-slate-950">{card.title}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600 sm:text-base">{card.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="modules" className="mx-auto max-w-7xl px-4 pb-18 sm:px-6 lg:px-8">
        <div className="grid gap-6 rounded-[2rem] border border-slate-200/80 bg-white/85 p-6 shadow-[0_20px_60px_rgba(15,23,42,0.06)] lg:grid-cols-[0.9fr_1.1fr] lg:p-8">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.22em] text-cyan-700">Coverage</p>
            <h2 className="mt-2 text-3xl font-black tracking-tight text-slate-950">Built for real hospital departments</h2>
            <p className="mt-4 text-sm leading-7 text-slate-600 sm:text-base">
              The system already covers administrative, clinical, diagnostic, pharmacy, finance, and compliance needs.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              'Patient registration and profile',
              'Doctor schedules and shifts',
              'Appointment queue and no-show handling',
              'Medical records and vital logs',
              'Lab workflow and report release',
              'Prescription writer and pharmacy',
              'Billing, refunds, and insurance',
              'Rooms, IPD, emergency, radiology, and surgery',
            ].map((item) => (
              <div key={item} className="rounded-2xl bg-slate-50 px-4 py-4 text-sm font-medium text-slate-700">
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="workflow" className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
        <div className="rounded-[2rem] bg-slate-950 px-6 py-8 text-white shadow-[0_30px_80px_rgba(15,23,42,0.2)] lg:px-8">
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-emerald-300">Patient journey</p>
          <h2 className="mt-2 text-3xl font-black tracking-tight">From arrival to discharge, one workflow.</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-4">
            {[
              'Patient registers and books an appointment',
              'Doctor, nurse, or receptionist manages the queue',
              'Lab, pharmacy, and billing continue the workflow',
              'Audit, notifications, and reports stay synchronized',
            ].map((item, index) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/6 p-5">
                <div className="text-sm font-black text-emerald-300">Step {index + 1}</div>
                <p className="mt-3 text-sm leading-7 text-slate-200">{item}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-2xl bg-white px-5 py-3 text-sm font-bold text-slate-950 transition hover:bg-slate-100"
            >
              Continue to Login
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-2xl border border-white/20 px-5 py-3 text-sm font-bold text-white transition hover:bg-white/8"
            >
              Visit Application Workspace
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
