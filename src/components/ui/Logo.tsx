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
      aria-label="NIEPMD Audiology and Speech home"
    >
      <img
        src="/niepmd-logo.png"
        alt="NIEPMD"
        className="h-10 w-auto shrink-0 object-contain sm:h-11"
      />
      {showText && (
        <span className="text-base leading-tight text-slate-900 sm:text-lg">
          NIEPMD
          <span className="ml-1.5 text-xs font-semibold text-brand-600 sm:text-sm">
            Audiology and Speech
          </span>
        </span>
      )}
    </Link>
  );
}
