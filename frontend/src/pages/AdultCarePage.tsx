import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Stethoscope,
  ShieldCheck,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  MessageSquare,
  Ear,
} from 'lucide-react';
import { PageHero } from '../components/ui/PageHero';
import { SectionHeading } from '../components/ui/SectionHeading';
import { Reveal } from '../components/ui/Reveal';
import { AccentIcon } from '../components/ui/AccentIcon';
import { LinkButton } from '../components/ui/Button';
import {
  adultSpeechSections,
  adultHearingSections,
  adultSections,
  specialTests,
  generalRecommendations,
  type AdultSection,
} from '../data/hearingData';

const accentMap = {
  blue: {
    border: 'border-blue-300 dark:border-blue-700',
    header: 'bg-blue-50 dark:bg-blue-900/30',
    numBg: 'bg-blue-500',
  },
  purple: {
    border: 'border-purple-300 dark:border-purple-700',
    header: 'bg-purple-50 dark:bg-purple-900/30',
    numBg: 'bg-purple-500',
  },
  green: {
    border: 'border-green-300 dark:border-green-700',
    header: 'bg-green-50 dark:bg-green-900/30',
    numBg: 'bg-green-500',
  },
  pink: {
    border: 'border-pink-300 dark:border-pink-700',
    header: 'bg-pink-50 dark:bg-pink-900/30',
    numBg: 'bg-pink-500',
  },
} as const;

type AccentKey = keyof typeof accentMap;

export function AdultCarePage() {
  const { hash } = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!hash) return;
    const id = hash.replace('#', '');
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
        title="For Adults — Speech & Hearing"
        description="Answer a short set of Yes / No / Not sure questions about your speech, language, or hearing concern. We’ll suggest what to check next."
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Adult Care' }]}
        accent="blue"
        icon={<Stethoscope size={13} />}
      />

      <SectionNav />

      <CategorySection
        id="section-speech"
        eyebrow="Section A — Speech and Language"
        title="Speech and language concerns"
        description="Five short checklists for word finding, fluency, clarity, voice, and swallowing."
        categories={adultSpeechSections}
        onOpen={(id) => navigate(`/ai-assistant?topic=${id}`)}
      />

      <CategorySection
        id="section-hearing"
        eyebrow="Section B — Audiology"
        title="Hearing and ear concerns"
        description="Five short checklists for hearing, ringing, balance, and ear pain."
        categories={adultHearingSections}
        onOpen={(id) => navigate(`/ai-assistant?topic=${id}`)}
        muted
      />

      <Reveal>
        <div className="container-page pb-4">
          <div className="flex items-center justify-center gap-3 rounded-2xl border border-brand-200 bg-brand-50 dark:bg-brand-900/20 dark:border-brand-800 px-6 py-4">
            <CheckCircle2 size={20} className="text-brand-600 dark:text-brand-300 shrink-0" />
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
              <span className="font-bold text-brand-700 dark:text-brand-300">Next Step:</span>{' '}
              Please consult an Audiologist / Speech-Language Pathologist / ENT for proper evaluation.
            </p>
            <CheckCircle2 size={20} className="text-brand-600 dark:text-brand-300 shrink-0" />
          </div>
        </div>
      </Reveal>

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
          <li>
            <a
              href="#section-speech"
              className="inline-flex items-center gap-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-purple-300 hover:text-purple-700 transition-colors"
            >
              <MessageSquare size={12} />
              Section A · Speech
            </a>
          </li>
          <li>
            <a
              href="#section-hearing"
              className="inline-flex items-center gap-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-blue-300 hover:text-blue-700 transition-colors"
            >
              <Ear size={12} />
              Section B · Hearing
            </a>
          </li>
          {adultSections.map((s) => (
            <li key={s.id}>
              <a
                href={`#${s.id}`}
                className="inline-flex items-center gap-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-brand-300 hover:text-brand-700 transition-colors"
              >
                <s.icon size={12} />
                {s.title}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function CategorySection({
  id,
  eyebrow,
  title,
  description,
  categories,
  onOpen,
  muted = false,
}: {
  id: string;
  eyebrow: string;
  title: string;
  description: string;
  categories: AdultSection[];
  onOpen: (id: string) => void;
  muted?: boolean;
}) {
  return (
    <section
      id={id}
      className={`scroll-mt-28 py-14 sm:py-20 ${muted ? 'bg-slate-50 dark:bg-slate-900/50' : ''}`}
    >
      <div className="container-page">
        <SectionHeading eyebrow={eyebrow} title={title} description={description} />

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map((s, i) => {
            const ac = accentMap[s.accent as AccentKey] ?? accentMap.blue;
            return (
              <Reveal key={s.id} delay={(i % 3) * 0.06}>
                <motion.button
                  type="button"
                  id={s.id}
                  onClick={() => onOpen(s.id)}
                  whileHover={{ y: -4, scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                  className={`w-full flex items-center gap-3 rounded-2xl border-2 px-5 py-4 scroll-mt-28 bg-white dark:bg-slate-900 shadow-sm hover:shadow-card-hover cursor-pointer transition-all text-left ${ac.border} ${ac.header}`}
                >
                  <span
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${ac.numBg}`}
                  >
                    {s.number}
                  </span>
                  <AccentIcon
                    icon={s.icon}
                    accent={s.accent === 'pink' ? 'purple' : s.accent}
                    size="sm"
                  />
                  <div className="flex-1 text-left">
                    <p className="text-sm font-bold uppercase tracking-wide text-slate-900 dark:text-white leading-tight">
                      {s.title}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      5 questions · Yes / No / Not sure
                    </p>
                  </div>
                  <ArrowRight size={16} className="shrink-0 text-slate-400" />
                </motion.button>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function SpecialTestsSection() {
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
              <ShieldCheck
                size={16}
                className="ml-auto text-green-500 opacity-0 group-hover:opacity-100 transition-opacity"
              />
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
            <LinkButton to="/register/relationship" variant="secondary" size="lg">
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
