import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Baby,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  FlaskConical,
  Lightbulb,
  AlertCircle,
  Heart,
  ShieldCheck,
} from 'lucide-react';
import { PageHero } from '../components/ui/PageHero';
import { SectionHeading } from '../components/ui/SectionHeading';
import { Reveal } from '../components/ui/Reveal';
import { AccentIcon } from '../components/ui/AccentIcon';
import { LinkButton } from '../components/ui/Button';
import { childCategories, childRecommendations, childTests } from '../data/childData';

// ── Accent colour map ─────────────────────────────────────────────────────────
const accentMap = {
  blue: {
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
  green: {
    border:  'border-green-300 dark:border-green-700',
    header:  'bg-green-50 dark:bg-green-900/30',
    badge:   'bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300',
    check:   'text-green-500',
    numBg:   'bg-green-500',
    chevron: 'text-green-500',
  },
  pink: {
    border:  'border-pink-300 dark:border-pink-700',
    header:  'bg-pink-50 dark:bg-pink-900/30',
    badge:   'bg-pink-100 text-pink-700 dark:bg-pink-900/50 dark:text-pink-300',
    check:   'text-pink-500',
    numBg:   'bg-pink-500',
    chevron: 'text-pink-500',
  },
} as const;

type AccentKey = keyof typeof accentMap;

export function ChildCarePage() {
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
        eyebrow="Child care"
        title="For Children — By Age Group"
        description="Hearing concerns in children change with age. Select the age group that fits your child to see the common signs, recommended tests, and what they help identify."
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Child Care' }]}
        accent="purple"
        icon={<Baby size={13} />}
      />

      <AgeNav />

      {/* ── 4 Age-group cards ─────────────────────────────────────────────── */}
      <section className="container-page py-14 sm:py-20">
        <SectionHeading
          eyebrow="Four age groups"
          title="Find your child's stage"
          description="Click a stage to see the common signs, recommended tests, and what the evaluation helps identify."
        />

        <div className="mt-12 grid gap-4 sm:grid-cols-2">
          {childCategories.map((c, i) => {
            const ac = accentMap[c.accent as AccentKey] ?? accentMap.blue;
            return (
              <Reveal key={c.id} delay={(i % 2) * 0.07}>
                <motion.button
                  type="button"
                  id={c.id}
                  onClick={() => navigate(`/ai-assistant?topic=${c.id}`)}
                  whileHover={{ y: -4, scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                  className={`w-full flex items-center gap-3 rounded-2xl border-2 px-5 py-4 scroll-mt-28 bg-white dark:bg-slate-900 shadow-sm hover:shadow-card-hover cursor-pointer transition-all text-left ${ac.border} ${ac.header}`}
                >
                  <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white ${ac.numBg}`}>
                    {c.number}
                  </span>
                  <AccentIcon icon={c.icon} accent={c.accent === 'pink' ? 'purple' : c.accent} size="sm" />
                  <div className="flex-1 text-left">
                    <p className="text-sm font-bold uppercase tracking-wide text-slate-900 dark:text-white leading-tight">
                      {c.title}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{c.ageRange}</p>
                  </div>
                  <ArrowRight size={16} className="shrink-0 text-slate-400" />
                </motion.button>
              </Reveal>
            );
          })}
        </div>

        {/* Next step banner */}
        <Reveal>
          <div className="mt-10 flex items-center justify-center gap-3 rounded-2xl border border-purple-200 bg-purple-50 dark:bg-purple-900/20 dark:border-purple-800 px-6 py-4">
            <CheckCircle2 size={20} className="text-purple-600 dark:text-purple-300 shrink-0" />
            <p className="text-sm font-medium text-slate-700 dark:text-slate-200">
              <span className="font-bold text-purple-700 dark:text-purple-300">Next Step:</span>{' '}
              Please consult a Paediatric Audiologist / ENT for proper evaluation and advice.
            </p>
            <CheckCircle2 size={20} className="text-purple-600 dark:text-purple-300 shrink-0" />
          </div>
        </Reveal>
      </section>

      {/* ── Child Tests Info ─────────────────────────────────────────────── */}
      <TestsInfoSection />

      {/* ── Recommendations ─────────────────────────────────────────────── */}
      <RecommendationsGrid />

      {/* ── CTA ──────────────────────────────────────────────────────────── */}
      <section className="container-page pb-8">
        <Reveal>
          <div className="rounded-3xl bg-gradient-to-br from-purple-600 to-brand-600 p-8 sm:p-12 text-center text-white shadow-card">
            <Heart size={28} className="mx-auto" />
            <h2 className="mt-4 text-2xl sm:text-3xl font-bold">We are here to help!</h2>
            <p className="mx-auto mt-3 max-w-xl text-white/85">
              Early action makes a big difference. Start a guided assessment or talk to our AI assistant.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <LinkButton to="/assessment" variant="secondary" size="lg">
                Start assessment <ArrowRight size={16} />
              </LinkButton>
              <Link to="/adult-care" className="btn bg-white/10 text-white hover:bg-white/20">
                Adult Care <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </Reveal>
      </section>
    </>
  );
}

function AgeNav() {
  return (
    <div className="border-y border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-900/40">
      <div className="container-page py-3 overflow-x-auto">
        <ul className="flex items-center gap-2 min-w-max">
          {childCategories.map((c) => (
            <li key={c.id}>
              <a
                href={`#${c.id}`}
                className="inline-flex items-center gap-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:border-purple-300 hover:text-purple-700 dark:hover:text-purple-300 transition-colors"
              >
                <c.icon size={12} />
                <span>{c.number}. {c.title}</span>
                <span className="text-slate-400">· {c.ageRange}</span>
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function TestsInfoSection() {
  const accentFor = (i: number): 'blue' | 'purple' | 'green' =>
    (['blue', 'purple', 'green', 'blue', 'purple', 'green', 'blue', 'purple'] as const)[i];

  return (
    <section className="bg-slate-50 dark:bg-slate-900/50 py-16 sm:py-20">
      <div className="container-page">
        <SectionHeading
          eyebrow="Diagnostic tests"
          title="Tests used in child hearing evaluation"
          description="Age-appropriate, non-invasive tests used by paediatric audiologists to assess hearing in children."
        />
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {childTests.map((t, i) => (
            <Reveal key={t.code} delay={(i % 4) * 0.06}>
              <motion.div
                whileHover={{ y: -4 }}
                className="card flex flex-col gap-3 p-4 h-full hover:shadow-card-hover transition-shadow"
              >
                <AccentIcon icon={t.icon} accent={accentFor(i)} size="sm" />
                <div>
                  <p className="text-sm font-bold text-slate-900 dark:text-white">{t.code}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">{t.name}</p>
                </div>
              </motion.div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}

function RecommendationsGrid() {
  return (
    <section className="container-page py-16 sm:py-20">
      <SectionHeading
        center
        eyebrow="Possible recommendations"
        title="What might come next"
        description="Depending on the assessment results, your audiologist may suggest one or more of the following."
      />
      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {childRecommendations.map((r, i) => (
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
