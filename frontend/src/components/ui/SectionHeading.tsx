import type { ReactNode } from 'react';
import { Reveal } from './Reveal';

interface SectionHeadingProps {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  center?: boolean;
  className?: string;
}

export function SectionHeading({
  eyebrow,
  title,
  description,
  center = false,
  className,
}: SectionHeadingProps) {
  return (
    <Reveal className={`${center ? 'text-center mx-auto max-w-2xl' : 'max-w-3xl'} ${className ?? ''}`}>
      {eyebrow && (
        <span
          className={`chip bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-200 ${
            center ? 'justify-center' : ''
          }`}
        >
          <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
          {eyebrow}
        </span>
      )}
      <h2 className="mt-4 text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white text-balance">
        {title}
      </h2>
      {description && (
        <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
          {description}
        </p>
      )}
    </Reveal>
  );
}
