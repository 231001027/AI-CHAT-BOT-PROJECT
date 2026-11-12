import { FormEvent, useRef, useState, type ChangeEvent, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { FileText, Paperclip, Printer, X } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { getSignedInStaff } from '@/lib/staffAuth';

const CONCERNS = [
  'Speech and language',
  'Fluency / stuttering',
  'Speech clarity',
  'Voice',
  'Feeding and swallowing',
  'Hearing',
];

interface GeneratedForm {
  patientId: string;
  patientName: string;
  age: string;
  gender: string;
  phone: string;
  concern: string;
  notes: string;
  files: string[];
  clinician: string;
  createdAt: string;
}

export function GenerateFormPage() {
  const staff = getSignedInStaff();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [patientId, setPatientId] = useState('');
  const [patientName, setPatientName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [phone, setPhone] = useState('');
  const [concern, setConcern] = useState(CONCERNS[0]);
  const [notes, setNotes] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [generated, setGenerated] = useState<GeneratedForm | null>(null);

  if (!staff) return <Navigate to="/login" replace />;
  const clinician = staff.name;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setGenerated({
      patientId: patientId.trim(),
      patientName: patientName.trim(),
      age: age.trim(),
      gender,
      phone: phone.trim(),
      concern,
      notes: notes.trim(),
      files: files.map((file) => file.name),
      clinician,
      createdAt: new Date().toLocaleString(),
    });
  }

  function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(event.target.files ?? []);
    if (picked.length) setFiles((current) => [...current, ...picked]);
    event.target.value = '';
  }

  return (
    <div className="container-page max-w-3xl py-10">
      <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">Staff</p>
      <h1 className="mt-2 text-2xl font-bold text-slate-900">Generate form</h1>
      <p className="mt-2 text-sm text-slate-600">
        Fill in the patient details, then generate a form you can print or save.
      </p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-soft print:hidden">
        <Field label="Patient ID no" id="patient-id">
          <input id="patient-id" required value={patientId} onChange={(e) => setPatientId(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Patient name" id="patient-name">
          <input id="patient-name" required value={patientName} onChange={(e) => setPatientName(e.target.value)} className={inputClass} />
        </Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Age" id="patient-age">
            <input id="patient-age" required inputMode="numeric" value={age} onChange={(e) => setAge(e.target.value)} className={inputClass} />
          </Field>
          <Field label="Gender" id="patient-gender">
            <select id="patient-gender" required value={gender} onChange={(e) => setGender(e.target.value)} className={inputClass}>
              <option value="">Select</option>
              <option>Female</option>
              <option>Male</option>
              <option>Other</option>
            </select>
          </Field>
        </div>
        <Field label="Phone" id="patient-phone">
          <input id="patient-phone" value={phone} onChange={(e) => setPhone(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Concern" id="patient-concern">
          <select id="patient-concern" value={concern} onChange={(e) => setConcern(e.target.value)} className={inputClass}>
            {CONCERNS.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </Field>
        <Field label="Notes" id="patient-notes">
          <textarea id="patient-notes" rows={4} value={notes} onChange={(e) => setNotes(e.target.value)} className={inputClass} />
        </Field>
        <div>
          <p className="text-sm font-medium text-slate-700">Files</p>
          <input ref={fileInputRef} type="file" multiple className="sr-only" onChange={handleFiles} />
          <Button type="button" variant="outline" className="mt-1.5" onClick={() => fileInputRef.current?.click()}>
            <Paperclip size={16} />
            Add file
          </Button>
          {files.length > 0 && (
            <ul className="mt-3 space-y-2">
              {files.map((file, index) => (
                <li key={`${file.name}-${file.lastModified}-${index}`} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700">
                  <span className="truncate">{file.name}</span>
                  <button
                    type="button"
                    className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800"
                    aria-label={`Remove ${file.name}`}
                    onClick={() => setFiles((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                  >
                    <X size={16} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <p className="text-sm text-slate-500">Prepared by {staff.name}</p>
        <Button type="submit">
          <FileText size={16} />
          Generate form
        </Button>
      </form>

      {generated && (
        <article className="mt-8 rounded-2xl border border-slate-300 bg-white p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">NIEPMD</p>
              <h2 className="mt-1 text-xl font-bold text-slate-900">Department of Speech, Hearing and Communication</h2>
              <p className="mt-1 text-sm text-slate-500">Clinical intake form · {generated.createdAt}</p>
            </div>
            <Button type="button" variant="outline" className="print:hidden" onClick={() => window.print()}>
              <Printer size={16} />
              Print
            </Button>
          </div>
          <dl className="mt-6 grid gap-4 sm:grid-cols-2">
            <Detail label="Patient ID no" value={generated.patientId} />
            <Detail label="Patient name" value={generated.patientName} />
            <Detail label="Age" value={generated.age} />
            <Detail label="Gender" value={generated.gender} />
            <Detail label="Phone" value={generated.phone || '—'} />
            <Detail label="Concern" value={generated.concern} />
            <Detail label="Prepared by" value={generated.clinician} />
          </dl>
          <div className="mt-4">
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Notes</dt>
            <dd className="mt-1 whitespace-pre-wrap text-sm text-slate-800">{generated.notes || '—'}</dd>
          </div>
          <div className="mt-4">
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">Files</dt>
            <dd className="mt-1 text-sm text-slate-800">{generated.files.length ? generated.files.join(', ') : '—'}</dd>
          </div>
        </article>
      )}
    </div>
  );
}

const inputClass = 'mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none ring-brand-500 focus:ring-2';

function Field({ id, label, children }: { id: string; label: string; children: ReactNode }) {
  return (
    <label className="block text-sm font-medium text-slate-700" htmlFor={id}>
      {label}
      {children}
    </label>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-slate-900">{value}</dd>
    </div>
  );
}
