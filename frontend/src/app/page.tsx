import Image from 'next/image';
import Link from 'next/link';

const journey = [
  'Register patient profile',
  'Book appointment',
  'Write appointment report',
  'AI analyzes history',
  'Recommend tests',
  'Track follow-up',
];

const modules = [
  ['Patient Timeline', 'Visits, diagnosis, medicines, reports, follow-up, and documents in one profile.'],
  ['AI Clinical Support', 'Possible causes, recommended tests, risk flag, and allergy warning for doctors.'],
  ['Hospital Operations', 'Appointments, doctors, lab workflow, prescriptions, billing, and notifications.'],
  ['Document Vault', 'Store lab reports, prescriptions, scans, and discharge summaries with the patient.'],
];

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <section className="relative overflow-hidden bg-[linear-gradient(135deg,#083344_0%,#0f766e_48%,#f8fafc_48%)]">
        <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
          <header className="flex items-center justify-between rounded-2xl border border-white/50 bg-white/90 px-5 py-3 shadow-sm">
            <div className="flex items-center gap-3">
              <Image src="/medimind-logo.svg" alt="MediMind" width={44} height={44} className="rounded-xl" priority />
              <div>
                <p className="text-lg font-black">MediMind</p>
                <p className="text-xs text-slate-500">Patient-centric hospital system</p>
              </div>
            </div>
            <nav className="flex items-center gap-3 text-sm font-semibold">
              <a href="#modules" className="hidden text-slate-600 hover:text-slate-950 sm:inline">Modules</a>
              <a href="#workflow" className="hidden text-slate-600 hover:text-slate-950 sm:inline">Workflow</a>
              <Link href="/login" className="rounded-xl bg-teal-700 px-4 py-2 text-white hover:bg-teal-800">Login</Link>
            </nav>
          </header>

          <div className="grid gap-10 py-16 lg:grid-cols-[1fr_0.9fr] lg:items-center">
            <div className="text-white">
              <p className="inline-flex rounded-full border border-white/25 bg-white/10 px-3 py-1 text-xs font-bold uppercase tracking-[0.2em]">
                Final year hospital project
              </p>
              <h1 className="mt-6 max-w-3xl text-4xl font-black leading-tight sm:text-5xl lg:text-6xl">
                Hospital Management System with Patient-Centric AI Clinical Decision Support
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-8 text-cyan-50">
                A complete hospital workspace where every appointment report becomes permanent patient history,
                and AI helps doctors review symptoms, allergies, risk, and recommended tests.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href="/login" className="rounded-2xl bg-white px-6 py-3 text-sm font-bold text-teal-800 shadow-lg hover:bg-slate-100">
                  Start Secure Login
                </Link>
                <Link href="/demo-flow" className="rounded-2xl border border-white/40 px-6 py-3 text-sm font-bold text-white hover:bg-white/10">
                  View Demo Flow
                </Link>
              </div>
            </div>

            <div className="rounded-[2rem] border border-white/70 bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.2)]">
              <p className="text-sm font-bold uppercase tracking-[0.2em] text-teal-700">Patient care summary</p>
              <h2 className="mt-3 text-2xl font-black">Sita Shrestha</h2>
              <div className="mt-4 grid gap-3 sm:grid-cols-2">
                {[
                  ['Risk', 'High'],
                  ['Allergy', 'Penicillin'],
                  ['History', 'Diabetes'],
                  ['AI Tests', 'CBC, CRP, X-Ray'],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-xs font-bold uppercase text-slate-500">{label}</p>
                    <p className="mt-1 font-bold text-slate-950">{value}</p>
                  </div>
                ))}
              </div>
              <div className="mt-5 rounded-2xl bg-teal-50 p-4 text-sm leading-6 text-teal-900">
                AI suggestions are decision support only. Final diagnosis and treatment are always made by the doctor.
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="modules" className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-teal-700">Core modules</p>
          <h2 className="mt-2 text-3xl font-black">Built for both hospital operations and patient management.</h2>
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {modules.map(([title, description]) => (
            <article key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-lg font-black">{title}</h3>
              <p className="mt-3 text-sm leading-7 text-slate-600">{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="workflow" className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
        <div className="rounded-[2rem] bg-slate-950 p-6 text-white shadow-xl">
          <p className="text-sm font-bold uppercase tracking-[0.22em] text-cyan-300">Working mechanism</p>
          <h2 className="mt-2 text-3xl font-black">From appointment to lifetime patient history.</h2>
          <div className="mt-8 grid gap-3 md:grid-cols-6">
            {journey.map((item, index) => (
              <div key={item} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-sm font-black text-cyan-300">0{index + 1}</p>
                <p className="mt-3 text-sm leading-6 text-slate-100">{item}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/login" className="rounded-2xl bg-white px-5 py-3 text-sm font-bold text-slate-950 hover:bg-slate-100">
              Continue to Login
            </Link>
            <Link href="/patients" className="rounded-2xl border border-white/20 px-5 py-3 text-sm font-bold text-white hover:bg-white/10">
              Open Patients
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
