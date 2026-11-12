import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Phone,
  Mail,
  MapPin,
  Clock,
  Send,
  CheckCircle2,
  MessageSquareHeart,
  Info,
  User,
} from 'lucide-react';
import { PageHero } from '../components/ui/PageHero';
import { Reveal } from '../components/ui/Reveal';
import { AccentIcon } from '../components/ui/AccentIcon';
import { submitContactForm } from '../services/api';

const PHONES = [
  { label: '044-27472113', href: 'tel:+914427472113' },
  { label: '044-27472046', href: 'tel:+914427472046' },
  { label: '044-27472104', href: 'tel:+914427472104' },
];
const TOLL_FREE = { label: '1800 425 0345', href: 'tel:18004250345' };
const EMAILS = [
  { label: 'niepmdhrd@gmail.com', href: 'mailto:niepmdhrd@gmail.com' },
  { label: 'niepmdshc@gmail.com', href: 'mailto:niepmdshc@gmail.com' },
];
const MAP_URL = 'https://maps.app.goo.gl/npi2aQb6SotMfLdy9';

export function ContactPage() {
  const [sent, setSent] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });

  const canSend = form.name.trim() && form.email.trim() && form.message.trim() && !sending;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSend) return;
    setSending(true);
    setError(null);
    try {
      await submitContactForm({
        name: form.name.trim(),
        email: form.email.trim(),
        subject: form.subject.trim() || undefined,
        message: form.message.trim(),
      });
      setSent(true);
      setForm({ name: '', email: '', subject: '', message: '' });
      window.setTimeout(() => setSent(false), 4000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      <PageHero
        eyebrow="Contact"
        title="We're here to listen"
        description="Have a question about hearing care, our pathways, or partnering with NIEPMD Department of Speech, Hearing and Communication? Reach out — we'd love to help."
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Contact' }]}
        accent="blue"
        icon={<MessageSquareHeart size={13} />}
      />

      <section className="container-page py-14 sm:py-20">
        <div className="grid gap-8 lg:grid-cols-3">
          <Reveal delay={0}>
            <div className="card h-full p-6 hover:shadow-card-hover transition-shadow">
              <AccentIcon icon={Phone} accent="blue" size="lg" />
              <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">Call us</h3>
              <ul className="mt-2 space-y-1">
                {PHONES.map((phone) => (
                  <li key={phone.href}>
                    <a href={phone.href} className="text-sm font-medium text-slate-800 hover:text-brand-700 dark:text-slate-100 dark:hover:text-brand-300">
                      {phone.label}
                    </a>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                Toll free:{' '}
                <a href={TOLL_FREE.href} className="font-medium text-brand-700 hover:underline dark:text-brand-300">
                  {TOLL_FREE.label}
                </a>
              </p>
            </div>
          </Reveal>

          <Reveal delay={0.08}>
            <div className="card h-full p-6 hover:shadow-card-hover transition-shadow">
              <AccentIcon icon={Mail} accent="purple" size="lg" />
              <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">Email us</h3>
              <ul className="mt-2 space-y-1">
                {EMAILS.map((email) => (
                  <li key={email.href}>
                    <a href={email.href} className="break-all text-sm font-medium text-slate-800 hover:text-brand-700 dark:text-slate-100 dark:hover:text-brand-300">
                      {email.label}
                    </a>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">We reply during working hours</p>
            </div>
          </Reveal>

          <Reveal delay={0.16}>
            <div className="card h-full p-6 hover:shadow-card-hover transition-shadow">
              <AccentIcon icon={MapPin} accent="green" size="lg" />
              <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">Visit us</h3>
              <a
                href={MAP_URL}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-block text-sm font-medium text-brand-700 hover:underline dark:text-brand-300"
              >
                Open location in Google Maps
              </a>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">NIEPMD Department of Speech, Hearing and Communication</p>
            </div>
          </Reveal>
        </div>

        <div className="mt-12 grid gap-8 lg:grid-cols-5">
          <Reveal className="lg:col-span-3">
            <form onSubmit={handleSubmit} className="card p-6 sm:p-8">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Send us a message</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Fields marked with * are required.</p>

              <div className="mt-6 grid gap-5 sm:grid-cols-2">
                <Field label="Full Name" required>
                  <input
                    type="text"
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    placeholder="Your name"
                    required
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900 transition-all"
                  />
                </Field>
                <Field label="Email" required>
                  <input
                    type="email"
                    value={form.email}
                    onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                    placeholder="you@example.com"
                    required
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900 transition-all"
                  />
                </Field>
              </div>
              <div className="mt-5">
                <Field label="Subject">
                  <input
                    type="text"
                    value={form.subject}
                    onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
                    placeholder="What's this about?"
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900 transition-all"
                  />
                </Field>
              </div>
              <div className="mt-5">
                <Field label="Message" required>
                  <textarea
                    value={form.message}
                    onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
                    placeholder="How can we help?"
                    required
                    rows={5}
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900 transition-all resize-y"
                  />
                </Field>
              </div>

              <button
                type="submit"
                disabled={!canSend}
                className="btn-primary mt-6 w-full sm:w-auto"
              >
                <Send size={16} /> {sending ? 'Sending…' : 'Send message'}
              </button>

              {error && (
                <p className="mt-4 text-sm text-red-600 dark:text-red-300" role="alert">
                  {error}
                </p>
              )}

              {sent && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 flex items-center gap-2 rounded-xl bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-200 px-4 py-3 text-sm"
                  role="status"
                >
                  <CheckCircle2 size={18} /> Thank you! Your message has been received.
                </motion.div>
              )}
            </form>
          </Reveal>

          <Reveal delay={0.1} className="lg:col-span-2">
            <div className="space-y-4">
              <div className="card p-6">
                <div className="flex items-center gap-2 text-brand-700 dark:text-brand-300">
                  <Info size={18} />
                  <h3 className="text-sm font-semibold">Emergency contact</h3>
                </div>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                  No emergency contact is available. Please use the numbers above during working hours, or call the toll-free line{' '}
                  <a href={TOLL_FREE.href} className="font-semibold text-brand-700 hover:underline dark:text-brand-300">
                    {TOLL_FREE.label}
                  </a>
                  .
                </p>
              </div>

              <div className="card p-6">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                  <Clock size={16} className="text-brand-500" /> Operating hours
                </h3>
                <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                  <li className="flex items-center justify-between"><span>Monday – Friday</span><span className="font-medium">9 AM – 5 PM</span></li>
                  <li className="flex items-center justify-between"><span>Saturday</span><span className="font-medium">9 AM – 1 PM</span></li>
                  <li className="flex items-center justify-between"><span>Sunday</span><span className="font-medium text-slate-400">Closed</span></li>
                </ul>
              </div>

              <div className="card p-6">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                  <User size={16} className="text-brand-500" /> Prefer to talk to the AI?
                </h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                  Our AI assistant is available 24/7 from the floating button at the bottom-right of any page.
                </p>
              </div>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}

function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-center gap-1 text-sm font-medium text-slate-700 dark:text-slate-200">
        {label}
        {required && <span className="text-brand-500">*</span>}
      </span>
      {children}
    </label>
  );
}
