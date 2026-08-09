import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Stethoscope,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  FlaskConical,
  Lightbulb,
  AlertCircle,
  ChevronDown,
  Volume2,
  Headphones,
  Brain,
  AudioLines,
  Waves,
  Mic,
  ScanLine,
  Gauge,
  Activity,
  EarOff,
} from 'lucide-react';
import { PageHero } from '../components/ui/PageHero';
import { SectionHeading } from '../components/ui/SectionHeading';
import { Reveal } from '../components/ui/Reveal';
import { AccentIcon } from '../components/ui/AccentIcon';
import { LinkButton } from '../components/ui/Button';
import { adultSections, specialTests, generalRecommendations } from '../data/hearingData';

// Accent colour map → Tailwind classes
const accentMap = {
  blue:   {
    border:  'border-blue-300 dark:border-blue-700',
    header:  'bg-blue-50 dark:bg-blue-900/30',
    badge:   'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300',
    check:   'text-blue-500',
    numBg:   'bg-blue-500',
    chevron: 'text-blue-500',
  },
  purple: {
    border:  'border-purple-300 dark:border-purple-700',
    header:  'bg-purple-50 dark:bg-purple-900/30',
    badge:   'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300',
    check:   'text-purple-500',
    numBg:   'bg-purple-500',
    chevron: 'text-purple-500',
  },
  green:  {
    border:  'border-green-300 dark:border-green-700',
    header:  'bg-green-50 dark:bg-green-900/30',
    badge:   'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300',
    check:   'text-green-500',
    numBg:   'bg-green-500',
    chevron: 'text-green-500',
  },
} as const;

export function AdultCarePage() {
  const { hash } = useLocation();
  const navigate = useNavigate();
  const [openId, setOpenId] = useState<string | null>(null);

  useEffect(() => {
    if (!hash) return;
    const id = hash.replace('#', '');
    setOpenId(id);
    const timer = setTimeout(() => {
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 120);
    return () => clearTimeout(timer);
  }, [hash]);

  return (
    <>
      <PageHero
        eyebrow="Adult care"
        title="For Adults / General Concerns"
        description="Six guided pathways covering the most common adult hearing concerns — each with common signs, recommended tests, and what the tests help identify."
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Adult Care' }]}
        accent="blue"
        icon={<Stethoscope size={13} />}
      />

      <SectionNav />

      {/* ── 6 Pathway cards ─────────────────────────────────────────────── */}
      <section className="container-page py-14 sm:py-20">
        <SectionHeading
          eyebrow="Six pathways"
          title="Choose your concern"
          description="Each pathway shows the signs to watch for, the tests an audiologist will recommend, and what those tests help identify."
        />

        <div className="mt-12 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {adultSections.map((s, i) => {
            const ac = accentMap[s.accent];
            const isOpen = openId === s.id;
            return (
              <Reveal key={s.id} delay={(i % 3) * 0.07}>
                <article
                  id={s.id}
                  className={`rounded-2xl border-2 overflow-hidden scroll-mt-28 bg-white dark:bg-slate-900 shadow-sm transition-shadow ${isOpen ? 'shadow-card-hover' : ''} ${ac.border}`}
                >
                  {/* Header — click to toggle */}
                  <button
                    type="button"
                    onClick={() => setOpenId(isOpen ? null : s.id)}
                    className={`w-full flex items-center gap-3 px-5 py-4 transition-colors ${ac.header} hover:brightness-95`}
                    aria-expanded={isOpen}
                  >
                    <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${ac.numBg}`}>
                      {s.number}
                    </span>
                    <AccentIcon icon={s.icon} accent={s.accent} size="sm" />
                    <h3 className="flex-1 text-left text-sm font-bold uppercase tracking-wide text-slate-900 dark:text-white leading-tight">
                      {s.title}
                    </h3>
                    <motion.span animate={{ rotate: isOpen ? 180 : 0 }} transition={{ duration: 0.25 }} className={ac.chevron}>
                      <ChevronDown size={18} />
                    </motion.span>
                  </button>

                  {/* Expanded panel */}
                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        key="panel"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                        className="overflow-hidden"
                      >
                        <div className="divide-y divide-slate-100 dark:divide-slate-800">
                          {/* Common Signs — each clickable → Q&A */}
                          <div className="px-5 py-4">
                            <p className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold mb-3 ${ac.badge}`}>
                              <AlertCircle size={11} /> Common Signs — click to start Q&A
                            </p>
                            <ul className="space-y-2">
                              {s.commonSigns.map((sign) => (
                                <li key={sign}>
                                  <button
                                    type="button"
                                    onClick={() => navigate(`/ai-assistant?topic=${s.id}&sign=${encodeURIComponent(sign)}`)}
                                    className="w-full flex items-center gap-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-3 py-2 text-sm text-left transition-all hover:shadow-sm hover:border-current group"
                                  >
                                    <CheckCircle2 size={14} className={`shrink-0 ${ac.check}`} />
                                    <span className="flex-1 text-slate-700 dark:text-slate-200">{sign}</span>
                                    <ArrowRight size={12} className="shrink-0 text-slate-300 group-hover:text-current transition-colors" />
                                  </button>
                                </li>
                              ))}
                            </ul>
                          </div>

                          {/* Recommended Tests */}
                          <div className="px-5 py-4">
                            <p className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold mb-3 ${ac.badge}`}>
                              <FlaskConical size={11} /> Recommended Tests
                            </p>
                            <ul className="space-y-1.5">
                              {s.tests.map((t) => (
                                <li key={t} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
                                  <CheckCircle2 size={14} className={`mt-0.5 shrink-0 ${ac.check}`} />
                                  {t}
                                </li>
                              ))}
                            </ul>
                          </div>

                          {/* What it helps */}
                          <div className="px-5 py-4">
                            <p className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold mb-2 ${ac.badge}`}>
                              <Lightbulb size={11} /> What it helps
                            </p>
                            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{s.whatItHelps}</p>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </article>
              </Reveal>
            );
          })}
        </div>

        {/* Next step banner */}
        <Reveal>
          <div className="mt-10 flex items-center justify-center gap-3 rounded-2xl border border-brand-200 bg-brand-50 dark:bg-brand-900/20 dark:border-brand-800 px-6 py-4">
            <CheckCircle2 size={20} className="text-brand-600 dark:text-brand-300 shrink-0" />
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
              <span className="font-bold text-brand-700 dark:text-brand-300">Next Step:</span>{' '}
              Please consult an Audiologist / ENT for proper evaluation and advice.
            </p>
            <CheckCircle2 size={20} className="text-brand-600 dark:text-brand-300 shrink-0" />
          </div>
        </Reveal>
      </section>

      <SpecialTestsSection />
      <RecommendationsSection />
      <FinalCTA />
    </>
  );
}

function SectionNav() {
  return (
    <div className="border-y border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40">
      <div className="container-page py-3 overflow-x-auto">
        <ul className="flex items-center gap-2 min-w-max">
          {adultSections.map((s) => (
            <li key={s.id}>
              <a
                href={`#${s.id}`}
                className="inline-flex items-center gap-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-brand-300 hover:text-brand-700 dark:hover:text-brand-300 transition-colors"
              >
                <s.icon size={12} />
                <span>{s.number}. {s.title}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function SpecialTestsSection() {
  // Split into non-speech and speech audiometry groups matching the image
  const nonSpeech = ['ABR', 'MLR', 'LLR', 'P300', 'P500'];
  const speechAudio = ['SRT', 'WRS', 'PB Test', 'SPIN'];

  const nonSpeechTests = specialTests.filter((t) => nonSpeech.includes(t.code));
  const speechTests = specialTests.filter((t) => speechAudio.includes(t.code));

  const accentFor = (i: number) =>
    (['blue', 'purple', 'green', 'blue', 'purple', 'green'][i] as 'blue' | 'purple' | 'green');

  return (
    <section className="bg-slate-50 dark:bg-slate-900/50 py-16 sm:py-20">
      <div className="container-page">
        <SectionHeading
          eyebrow="Special tests"
          title="Special Tests"
          description="In case of need for identifying specific functions of the auditory system."
        />

        {/* Non-speech */}
        <div className="mt-10">
          <h3 className="mb-5 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-1.5 text-sm font-bold text-white">
            Special Tests (Non-Speech)
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {nonSpeechTests.map((t, i) => (
              <Reveal key={t.code} delay={i * 0.05}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="card flex flex-col gap-3 p-4 h-full hover:shadow-card-hover transition-shadow"
                >
                  <AccentIcon icon={t.icon} accent={accentFor(i)} size="sm" />
                  <div>
                    <p className="text-sm font-bold text-slate-900 dark:text-white">{t.code}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{t.name}</p>
                    <p className="mt-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{t.description}</p>
                  </div>
                </motion.div>
              </Reveal>
            ))}
          </div>
        </div>

        {/* Speech audiometry */}
        <div className="mt-8">
          <h3 className="mb-5 inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-1.5 text-sm font-bold text-white">
            Special Speech Audiometry Tests
          </h3>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {speechTests.map((t, i) => (
              <Reveal key={t.code} delay={i * 0.05}>
                <motion.div
                  whileHover={{ y: -4 }}
                  className="card flex flex-col gap-3 p-4 h-full hover:shadow-card-hover transition-shadow"
                >
                  <AccentIcon icon={t.icon} accent={accentFor(i + 2)} size="sm" />
                  <div>
                    <p className="text-sm font-bold text-slate-900 dark:text-white">{t.code}</p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{t.name}</p>
                    <p className="mt-2 text-xs text-slate-600 dark:text-slate-300 leading-relaxed">{t.description}</p>
                  </div>
                </motion.div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function RecommendationsSection() {
  return (
    <section className="container-page py-16 sm:py-20">
      <SectionHeading
        center
        eyebrow="Everyday care"
        title="General Recommendations"
        description="Simple, evidence-based habits that protect your hearing every day."
      />
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {generalRecommendations.map((r, i) => (
          <Reveal key={r.title} delay={(i % 3) * 0.06}>
            <div className="group flex items-center gap-4 card p-5 hover:shadow-card-hover transition-shadow">
              <AccentIcon icon={r.icon} accent={r.accent} className="group-hover:scale-110 transition-transform" />
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-100">{r.title}</span>
              <ShieldCheck size={16} className="ml-auto text-green-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function FinalCTA() {
  return (
    <section className="container-page pb-8">
      <Reveal>
        <div className="rounded-3xl bg-gradient-to-br from-brand-600 to-purple-600 p-8 sm:p-12 text-center text-white shadow-card">
          <Sparkles size={28} className="mx-auto" />
          <h2 className="mt-4 text-2xl sm:text-3xl font-bold">We are here to help!</h2>
          <p className="mx-auto mt-3 max-w-xl text-white/85">
            Let our AI assistant guide you through a few questions and recommend the right tests for your concern.
          </p>
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            <LinkButton to="/take-test" variant="secondary" size="lg">
              Take Test <ArrowRight size={16} />
            </LinkButton>
            <Link to="/child-care" className="btn bg-white/10 text-white hover:bg-white/20">
              Child Care <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
