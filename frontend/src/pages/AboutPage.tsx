import { motion } from 'framer-motion';
import {
  Target,
  HeartHandshake,
  Sparkles,
  Users,
  Stethoscope,
  ShieldCheck,
  Baby,
  Ear,
  CheckCircle2,
} from 'lucide-react';
import { PageHero } from '../components/ui/PageHero';
import { SectionHeading } from '../components/ui/SectionHeading';
import { Reveal } from '../components/ui/Reveal';
import { AccentIcon } from '../components/ui/AccentIcon';
import { LinkButton } from '../components/ui/Button';

const values = [
  { title: 'Early Detection', icon: Sparkles, accent: 'blue' as const, desc: 'We believe hearing concerns are best addressed early — at every age.' },
  { title: 'Compassion First', icon: HeartHandshake, accent: 'purple' as const, desc: 'Every interaction is calm, respectful and free of judgement.' },
  { title: 'Accessibility', icon: ShieldCheck, accent: 'green' as const, desc: 'High-contrast, keyboard-friendly, screen-reader ready — for everyone.' },
];

const pillars = [
  { title: 'For Adults', icon: Stethoscope, accent: 'blue' as const, desc: 'Six adult pathways from hearing difficulty to balance problems.' },
  { title: 'For Children', icon: Baby, accent: 'purple' as const, desc: 'Speech, language, and hearing checklists for children — guided Yes / No questions.' },
  { title: 'AI Guidance', icon: Ear, accent: 'green' as const, desc: 'A mock AI assistant offering instant, caring next steps.' },
];

const milestones = [
  { year: '2024', title: 'Concept born', desc: 'NIEPMD Audiology Department started as an idea to make hearing screening guidance accessible to all.' },
  { year: '2025', title: 'Pathways built', desc: 'Adult and child care pathways designed with audiologist-friendly test recommendations.' },
  { year: '2026', title: 'AI assistant launched', desc: 'A guided assistant now helps users from concern to recommended care.' },
];

export function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About us"
        title="Hearing care, made approachable"
        description="NIEPMD Audiology Department is an AI-powered hearing Take Test assistant built to help hearing-impaired children and adults understand their concerns and find the right next step."
        crumbs={[{ label: 'Home', to: '/' }, { label: 'About' }]}
        accent="green"
        icon={<HeartHandshake size={13} />}
      />

      <section className="container-page py-16 sm:py-20">
        <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
          <Reveal>
            <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">
              <span className="h-1.5 w-1.5 rounded-full bg-brand-500" /> Our mission
            </span>
            <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white text-balance">
              Connecting every ear to the care it deserves
            </h2>
            <p className="mt-5 text-slate-600 dark:text-slate-300 leading-relaxed">
              Millions of children and adults live with undiagnosed hearing concerns. NIEPMD
              Audiology Department lowers the first barrier — understanding what might be wrong and what to do next —
              with a friendly, AI-guided experience that works on any device.
            </p>
            <ul className="mt-6 space-y-2.5">
              {[
                'No sign-up, no cost, no data leaves your device',
                'Guidance tailored for both children and adults',
                'Recommendations aligned with standard audiology practice',
              ].map((t) => (
                <li key={t} className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
                  <CheckCircle2 size={18} className="text-green-500" /> {t}
                </li>
              ))}
            </ul>
          </Reveal>

          <Reveal delay={0.1}>
            <div className="relative">
              <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-brand-500 to-purple-500 opacity-10 blur-2xl" aria-hidden="true" />
              <div className="relative grid grid-cols-2 gap-4">
                <StatCard icon={Users} value="2" label="Care pathways" accent="blue" />
                <StatCard icon={Stethoscope} value="15+" label="Tests explained" accent="purple" />
                <StatCard icon={Baby} value="4" label="Child age groups" accent="green" />
                <StatCard icon={Ear} value="20" label="AI responses" accent="blue" />
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="bg-slate-50 dark:bg-slate-900/50 py-16 sm:py-20">
        <div className="container-page">
          <SectionHeading center eyebrow="What we value" title="Principles that guide us" />
          <div className="mt-12 grid gap-6 sm:grid-cols-3">
            {values.map((v, i) => (
              <Reveal key={v.title} delay={i * 0.08}>
                <div className="card h-full p-6 text-center hover:shadow-card-hover transition-shadow">
                  <div className="flex justify-center">
                    <AccentIcon icon={v.icon} accent={v.accent} size="lg" />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">{v.title}</h3>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{v.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="container-page py-16 sm:py-20">
        <SectionHeading center eyebrow="What we offer" title="Three pillars of NIEPMD Audiology" />
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {pillars.map((p, i) => (
            <Reveal key={p.title} delay={i * 0.08}>
              <div className="group card h-full p-6 hover:shadow-card-hover transition-shadow">
                <AccentIcon icon={p.icon} accent={p.accent} size="lg" className="group-hover:scale-110 transition-transform" />
                <h3 className="mt-4 text-lg font-semibold text-slate-900 dark:text-white">{p.title}</h3>
                <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{p.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="container-page pb-16 sm:pb-20">
        <SectionHeading eyebrow="Our journey" title="How we got here" />
        <div className="mt-12 relative">
          <div className="absolute left-4 top-0 h-full w-px bg-gradient-to-b from-brand-500 to-purple-500 sm:left-1/2" aria-hidden="true" />
          <div className="space-y-8">
            {milestones.map((m, i) => (
              <Reveal key={m.year} delay={i * 0.05}>
                <div className={`relative flex items-start gap-6 sm:w-1/2 ${i % 2 === 0 ? 'sm:ml-auto sm:flex-row' : 'sm:flex-row-reverse sm:text-right'}`}>
                  <span className="absolute -left-0.5 top-1 flex h-8 w-8 items-center justify-center rounded-full bg-white dark:bg-slate-900 ring-4 ring-brand-100 dark:ring-brand-900 sm:-left-4" style={i % 2 === 0 ? { left: 'auto', right: '-1rem' } : undefined}>
                    <span className="h-3 w-3 rounded-full bg-brand-500" />
                  </span>
                  <div className="ml-12 sm:ml-0 card p-5 flex-1">
                    <span className="chip bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-200">{m.year}</span>
                    <h3 className="mt-2 text-base font-semibold text-slate-900 dark:text-white">{m.title}</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{m.desc}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section className="container-page pb-8">
        <Reveal>
          <div className="rounded-3xl bg-gradient-to-br from-green-600 to-brand-600 p-8 sm:p-12 text-center text-white shadow-card">
            <Target size={28} className="mx-auto" />
            <h2 className="mt-4 text-2xl sm:text-3xl font-bold">Join us in making hearing care accessible</h2>
            <p className="mx-auto mt-3 max-w-xl text-white/85">
              Try the Take Test, explore the pathways, or talk to our AI assistant today.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <LinkButton to="/register/relationship" variant="secondary" size="lg">Take Test</LinkButton>
              <LinkButton to="/contact" variant="secondary" size="lg">Contact us</LinkButton>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}

function StatCard({ icon: Icon, value, label, accent }: { icon: typeof Target; value: string; label: string; accent: 'blue' | 'purple' | 'green' }) {
  const styles = {
    blue: 'from-brand-500 to-brand-700',
    purple: 'from-purple-500 to-purple-700',
    green: 'from-green-500 to-green-700',
  };
  return (
    <motion.div whileHover={{ y: -4 }} className={`rounded-2xl bg-gradient-to-br ${styles[accent]} p-5 text-white shadow-soft`}>
      <Icon size={22} className="text-white/80" />
      <p className="mt-2 text-2xl font-bold">{value}</p>
      <p className="text-xs text-white/80">{label}</p>
    </motion.div>
  );
}
