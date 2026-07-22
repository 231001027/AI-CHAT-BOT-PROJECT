import { Ear } from 'lucide-react';
import { Link } from 'react-router-dom';

interface LogoProps {
  className?: string;
  showText?: boolean;
}

export function Logo({ className = '', showText = true }: LogoProps) {
  return (
    <Link
      to="/"
      className={`flex items-center gap-2.5 font-display font-extrabold ${className}`}
      aria-label="HearConnect AI home"
    >
      <span className="relative inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 via-brand-600 to-purple-500 text-white shadow-soft">
        <Ear size={20} strokeWidth={2.4} />
        <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-green-500 ring-2 ring-white dark:ring-slate-950" />
      </span>
      {showText && (
        <span className="text-lg leading-none">
          <span className="text-slate-900 dark:text-white">Hear</span>
          <span className="text-brand-600 dark:text-brand-400">Connect</span>
          <span className="ml-1 text-xs align-top text-slate-400 dark:text-slate-500 font-semibold">
            AI
          </span>
        </span>
      )}
    </Link>
  );
}
