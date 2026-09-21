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
      aria-label="NIEPMD Department of Speech, Hearing and Communication home"
    >
      <img
        src="/niepmd-logo.png"
        alt="NIEPMD"
        className="h-10 w-auto shrink-0 object-contain sm:h-11"
      />
      {showText && (
        <span className="flex min-w-0 flex-col leading-tight">
          <span className="text-base font-extrabold text-slate-900 sm:text-lg">NIEPMD</span>
          <span className="text-[11px] font-semibold text-brand-600 sm:text-xs">
            Department of Speech, Hearing and Communication
          </span>
        </span>
      )}
    </Link>
  );
}
