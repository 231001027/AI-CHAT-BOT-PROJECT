import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

interface PageHeroProps {
  eyebrow: string;
  title: ReactNode;
  description: ReactNode;
  crumbs?: { label: string; to?: string }[];
  accent?: 'blue' | 'purple' | 'green';
  icon?: ReactNode;
}

const gradients = {
  blue: 'from-brand-500 to-brand-700',
  purple: 'from-purple-500 to-purple-700',
  green: 'from-green-500 to-green-700',
};

export function PageHero({ eyebrow, title, description, crumbs, accent = 'blue', icon }: PageHeroProps) {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-brand-50/70 to-white dark:from-slate-900 dark:to-slate-950">
      <div
        className={`absolute -right-24 -top-24 h-72 w-72 rounded-full bg-gradient-to-br ${gradients[accent]} opacity-10 blur-3xl`}
        aria-hidden="true"
      />
      <div
        className="absolute left-0 top-0 h-full w-full bg-grid-light opacity-40 dark:opacity-10"
        aria-hidden="true"
      />
      <div className="container-page relative py-14 sm:py-20">
        {crumbs && crumbs.length > 0 && (
          <nav aria-label="Breadcrumb" className="mb-6">
            <ol className="flex flex-wrap items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
              {crumbs.map((c, i) => (
                <li key={c.label} className="flex items-center gap-1.5">
                  {c.to ? (
                    <Link to={c.to} className="hover:text-brand-600 dark:hover:text-brand-300">
                      {c.label}
                    </Link>
                  ) : (
                    <span className="text-slate-700 dark:text-slate-200 font-medium">{c.label}</span>
                  )}
                  {i < crumbs.length - 1 && <ChevronRight size={13} className="text-slate-300" />}
                </li>
              ))}
            </ol>
          </nav>
        )}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-3xl"
        >
          <span className="chip bg-white text-brand-700 border border-brand-100 dark:bg-slate-800 dark:text-brand-300 dark:border-slate-700">
            {icon}
            {eyebrow}
          </span>
          <h1 className="mt-4 text-4xl sm:text-5xl font-bold text-slate-900 dark:text-white text-balance">
            {title}
          </h1>
          <p className="mt-5 text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
            {description}
          </p>
        </motion.div>
      </div>
    </section>
  );
}
