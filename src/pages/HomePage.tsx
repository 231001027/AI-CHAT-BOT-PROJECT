import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  MessageSquareHeart,
  ScanSearch,
  Baby,
  ShieldCheck,
  ArrowRight,
  Stethoscope,
  Volume2,
  Brain,
  CheckCircle2,
  Star,
  Users,
  Activity,
} from 'lucide-react';
import { LinkButton } from '../components/ui/Button';
import { Reveal } from '../components/ui/Reveal';
import { SectionHeading } from '../components/ui/SectionHeading';
import { AccentIcon } from '../components/ui/AccentIcon';
import { hearingProblems } from '../data/hearingData';

const features = [
  { title: 'Early Detection', icon: ScanSearch, accent: 'blue' as const, desc: 'Spot hearing concerns early, when intervention works best.' },
  { title: 'Better Communication', icon: MessageSquareHeart, accent: 'purple' as const, desc: 'Guidance that improves how you connect and converse.' },
  { title: 'Child Friendly', icon: Baby, accent: 'green' as const, desc: 'Calm, age-aware Take Tests designed for little ones.' },
  { title: 'AI Guidance', icon: Sparkles, accent: 'blue' as const, desc: 'Instant, personalised next steps from our AI assistant.' },
];

const stats = [
  { value: '20+', label: 'AI-guided responses', icon: Brain },
  { value: '15+', label: 'Hearing tests explained', icon: Volume2 },
  { value: '6', label: 'Adult care pathways', icon: Stethoscope },
  { value: '4', label: 'Child age groups', icon: Baby },
];

const steps = [
  { title: 'Tell us who needs help', desc: 'Yourself, your child, or someone you care for.', icon: Users },
  { title: 'Share a few details', desc: 'Quick, private intake — no account needed.', icon: ShieldCheck },
  { title: 'Chat with the AI assistant', desc: 'Describe the concern in your own words.', icon: MessageSquareHeart },
  { title: 'Get a tailored care pathway', desc: 'Recommended tests and next steps, instantly.', icon: ArrowRight },
];

export function HomePage() {
  return (
    <>
      <Hero />
      <FeaturesSection />
      <StatsSection />
      <HowItWorks />
      <ProblemsPreview />
      <CTASection />
    </>
  );
}

function Hero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-brand-50/60 via-white to-white dark:from-slate-900 dark:via-slate-950 dark:to-slate-950">
      <div className="absolute inset-0 bg-grid-light opacity-40 dark:opacity-[0.07]" aria-hidden="true" />
      <div className="absolute -right-32 -top-32 h-96 w-96 rounded-full bg-brand-500/10 blur-3xl" aria-hidden="true" />
      <div className="absolute -left-24 top-40 h-72 w-72 rounded-full bg-purple-500/10 blur-3xl" aria-hidden="true" />

      <div className="container-page relative max-w-3xl py-16 lg:py-24">
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        >
          <span className="chip bg-white text-brand-700 border border-brand-100 shadow-soft">
            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
            AI-powered hearing care
          </span>
          <div className="mt-5 flex flex-col gap-5 sm:flex-row sm:items-center">
            <img
              src="/niepmd-logo.png"
              alt="NIEPMD logo"
              className="h-20 w-auto shrink-0 object-contain sm:h-24 lg:h-28"
            />
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-900 text-balance leading-[1.15]">
              Welcome to{' '}
              <span className="bg-gradient-to-r from-brand-600 via-brand-500 to-purple-500 bg-clip-text text-transparent">
                NIEPMD Audiology Department
              </span>
            </h1>
          </div>
          <p className="mt-5 text-lg sm:text-xl text-slate-600 dark:text-slate-300 leading-relaxed max-w-xl">
            An AI-powered hearing Take Test assistant helping children and adults identify
            hearing-related concerns.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <LinkButton to="/take-test" size="lg" aria-label="Take Test">
              <Sparkles size={18} />
              Take Test
            </LinkButton>
            <LinkButton to="/ai-assistant" variant="secondary" size="lg" aria-label="Talk to AI">
              <MessageSquareHeart size={18} />
              Talk to AI
            </LinkButton>
          </div>
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-slate-500 dark:text-slate-400">
            <span className="inline-flex items-center gap-2">
              <CheckCircle2 size={16} className="text-green-500" /> No sign-up required
            </span>
            <span className="inline-flex items-center gap-2">
              <CheckCircle2 size={16} className="text-green-500" /> Private &amp; secure
            </span>
            <span className="inline-flex items-center gap-2">
              <CheckCircle2 size={16} className="text-green-500" /> Works on any device
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function FeaturesSection() {
  return (
    <section className="container-page py-16 sm:py-20">
      <SectionHeading
        center
        eyebrow="Why NIEPMD Audiology"
        title="Care that listens first"
        description="Four principles guide every Take Test and every conversation at NIEPMD Audiology Department."
      />
      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {features.map((f, i) => (
          <Reveal key={f.title} delay={i * 0.08}>
            <div className="group h-full card p-6 hover:shadow-card-hover transition-shadow">
              <AccentIcon icon={f.icon} accent={f.accent} size="lg" className="group-hover:scale-110 transition-transform" />
              <h3 className="mt-5 text-lg font-semibold text-slate-900 dark:text-white">{f.title}</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{f.desc}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function StatsSection() {
  return (
    <section className="container-page pb-4">
      <Reveal>
        <div className="grid grid-cols-2 gap-4 rounded-3xl bg-gradient-to-br from-brand-600 to-purple-600 p-8 sm:p-10 text-white shadow-card lg:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="flex flex-col items-center text-center">
              <s.icon size={22} className="text-white/80" />
              <span className="mt-2 text-3xl sm:text-4xl font-bold">{s.value}</span>
              <span className="mt-1 text-xs sm:text-sm text-white/80">{s.label}</span>
            </div>
          ))}
        </div>
      </Reveal>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="container-page py-16 sm:py-24">
      <SectionHeading
        center
        eyebrow="How it works"
        title="A clear path from concern to care"
        description="Our guided Take Test takes you from a first question to a personalised recommendation in minutes."
      />
      <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {steps.map((s, i) => (
          <Reveal key={s.title} delay={i * 0.1}>
            <div className="relative h-full card p-6">
              <span className="absolute right-5 top-5 text-5xl font-bold text-brand-50 dark:text-slate-800 select-none" aria-hidden="true">
                {i + 1}
              </span>
              <AccentIcon icon={s.icon} accent="blue" />
              <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">{s.title}</h3>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{s.desc}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function ProblemsPreview() {
  return (
    <section className="bg-slate-50 dark:bg-slate-900/50 py-16 sm:py-24">
      <div className="container-page">
        <SectionHeading
          eyebrow="Hearing concerns"
          title="Find guidance for your specific concern"
          description="Each pathway leads to tailored questions and the hearing tests your audiologist is likely to recommend."
        />
        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {hearingProblems.map((p, i) => (
            <Reveal key={p.id} delay={i * 0.06}>
              <Link
                to={p.route}
                className="group block h-full card p-6 hover:shadow-card-hover transition-all hover:-translate-y-1"
              >
                <div className="flex items-center justify-between">
                  <AccentIcon icon={p.icon} accent={p.accent} size="lg" />
                  <ArrowRight size={18} className="text-slate-300 group-hover:text-brand-600 group-hover:translate-x-1 transition-all" />
                </div>
                <h3 className="mt-5 text-lg font-semibold text-slate-900 dark:text-white">{p.title}</h3>
                <ul className="mt-3 space-y-1.5">
                  {p.symptoms.map((s) => (
                    <li key={s} className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
                      <span className="h-1.5 w-1.5 rounded-full bg-brand-400" />
                      {s}
                    </li>
                  ))}
                </ul>
              </Link>
            </Reveal>
          ))}
          <Reveal delay={0.3}>
            <Link
              to="/take-test"
              className="group flex h-full flex-col justify-center items-center gap-3 rounded-2xl border-2 border-dashed border-brand-200 bg-brand-50/50 p-6 text-center hover:bg-brand-50 dark:border-brand-900 dark:bg-brand-900/20 dark:hover:bg-brand-900/30 transition-colors"
            >
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-white">
                <Sparkles size={26} />
              </span>
              <p className="text-base font-semibold text-brand-700 dark:text-brand-300">Not sure where to start?</p>
              <p className="text-sm text-slate-600 dark:text-slate-400">Take the full guided Take Test</p>
            </Link>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className="container-page py-16 sm:py-24">
      <Reveal>
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-brand-900 to-purple-900 px-8 py-14 text-center text-white shadow-card sm:px-14">
          <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-brand-500/30 blur-3xl" aria-hidden="true" />
          <div className="absolute -left-16 -bottom-16 h-56 w-56 rounded-full bg-purple-500/30 blur-3xl" aria-hidden="true" />
          <div className="relative">
            <span className="chip bg-white/10 text-white">
              <Star size={12} className="fill-white" />
              Ready when you are
            </span>
            <h2 className="mx-auto mt-4 max-w-2xl text-3xl sm:text-4xl font-bold text-balance">
              Take the first step toward better hearing today
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-white/80">
              Our AI assistant is here to help, 24/7. No appointments, no waiting — just clear,
              caring guidance.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <LinkButton to="/take-test" size="lg">
                <Sparkles size={18} />
                Take Test
              </LinkButton>
              <LinkButton to="/contact" variant="secondary" size="lg">
                <Activity size={18} />
                Contact a specialist
              </LinkButton>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
