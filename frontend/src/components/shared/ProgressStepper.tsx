import { Check } from 'lucide-react';
import { cn } from '@/lib/utils';

const STEPS = [
  { key: 'register', label: 'Register' },
  { key: 'category', label: 'Category' },
  { key: 'questions', label: 'Questions' },
  { key: 'summary', label: 'Summary' },
  { key: 'results', label: 'Results' },
] as const;

export type StepKey = (typeof STEPS)[number]['key'];

export function ProgressStepper({ current }: { current: StepKey }) {
  const idx = STEPS.findIndex((s) => s.key === current);
  return (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex flex-wrap items-center gap-2 sm:gap-0">
        {STEPS.map((step, i) => {
          const done = i < idx;
          const active = i === idx;
          return (
            <li key={step.key} className="flex items-center">
              <div
                className={cn(
                  'flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold sm:text-sm',
                  done && 'bg-green-50 text-green-700',
                  active && 'bg-brand-50 text-brand-700',
                  !done && !active && 'text-slate-400',
                )}
              >
                <span
                  className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full text-[11px]',
                    done && 'bg-green-500 text-white',
                    active && 'bg-brand-500 text-white',
                    !done && !active && 'bg-slate-200 text-slate-500',
                  )}
                >
                  {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
                </span>
                {step.label}
              </div>
              {i < STEPS.length - 1 && (
                <span className="mx-1 hidden h-px w-6 bg-slate-200 sm:block" aria-hidden />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
