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
  Siren,
  User,
} from 'lucide-react';
import { PageHero } from '../components/ui/PageHero';
import { Reveal } from '../components/ui/Reveal';
import { AccentIcon } from '../components/ui/AccentIcon';

const contactCards = [
  { icon: Phone, title: 'Call us', value: '1800-123-456', sub: 'Mon–Sat, 9 AM – 7 PM', accent: 'blue' as const },
  { icon: Mail, title: 'Email us', value: 'care@hearconnect.ai', sub: 'We reply within 24 hours', accent: 'purple' as const },
  { icon: MapPin, title: 'Visit us', value: 'Audiology Wing, City Care Hospital', sub: 'Central District, City 001', accent: 'green' as const },
];

export function ContactPage() {
  const [sent, setSent] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });

  const canSend = form.name.trim() && form.email.trim() && form.message.trim();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSend) return;
    setSent(true);
    setForm({ name: '', email: '', subject: '', message: '' });
    window.setTimeout(() => setSent(false), 4000);
  };

  return (
    <>
      <PageHero
        eyebrow="Contact"
        title="We're here to listen"
        description="Have a question about hearing care, our pathways, or partnering with HearConnect AI? Reach out — we'd love to help."
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Contact' }]}
        accent="blue"
        icon={<MessageSquareHeart size={13} />}
      />

      <section className="container-page py-14 sm:py-20">
        <div className="grid gap-8 lg:grid-cols-3">
          {contactCards.map((c, i) => (
            <Reveal key={c.title} delay={i * 0.08}>
              <div className="card h-full p-6 hover:shadow-card-hover transition-shadow">
                <AccentIcon icon={c.icon} accent={c.accent} size="lg" />
                <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">{c.title}</h3>
                <p className="mt-1 text-sm font-medium text-slate-800 dark:text-slate-100">{c.value}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{c.sub}</p>
              </div>
            </Reveal>
          ))}
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
                <Send size={16} /> Send message
              </button>

              {sent && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 flex items-center gap-2 rounded-xl bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-200 px-4 py-3 text-sm"
                  role="status"
                >
                  <CheckCircle2 size={18} /> Thank you! Your message has been recorded (demo only).
                </motion.div>
              )}
            </form>
          </Reveal>

          <Reveal delay={0.1} className="lg:col-span-2">
            <div className="space-y-4">
              <div className="card p-6">
                <div className="flex items-center gap-2 text-brand-700 dark:text-brand-300">
                  <Siren size={18} />
                  <h3 className="text-sm font-semibold">Emergency hearing helpline</h3>
                </div>
                <a href="tel:+911800123456" className="mt-2 block text-2xl font-bold text-slate-900 dark:text-white">
                  1800-123-456
                </a>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  For sudden hearing loss or severe ear pain, call immediately.
                </p>
              </div>

              <div className="card p-6">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                  <Clock size={16} className="text-brand-500" /> Operating hours
                </h3>
                <ul className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                  <li className="flex items-center justify-between"><span>Monday – Friday</span><span className="font-medium">9 AM – 7 PM</span></li>
                  <li className="flex items-center justify-between"><span>Saturday</span><span className="font-medium">10 AM – 4 PM</span></li>
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
