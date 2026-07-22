import type { LucideIcon } from 'lucide-react';

type Accent = 'blue' | 'purple' | 'green';

const styles: Record<Accent, string> = {
  blue: 'bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-200',
  purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/40 dark:text-purple-200',
  green: 'bg-green-50 text-green-600 dark:bg-green-900/40 dark:text-green-200',
};

const ring: Record<Accent, string> = {
  blue: 'group-hover:ring-brand-200 dark:group-hover:ring-brand-800',
  purple: 'group-hover:ring-purple-200 dark:group-hover:ring-purple-800',
  green: 'group-hover:ring-green-200 dark:group-hover:ring-green-800',
};

interface AccentIconProps {
  icon: LucideIcon;
  accent?: Accent;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizes = {
  sm: 'h-9 w-9 rounded-lg',
  md: 'h-12 w-12 rounded-xl',
  lg: 'h-14 w-14 rounded-2xl',
};

const iconSizes = {
  sm: 18,
  md: 22,
  lg: 28,
};

export function AccentIcon({ icon: Icon, accent = 'blue', size = 'md', className }: AccentIconProps) {
  return (
    <span
      className={`inline-flex items-center justify-center ${sizes[size]} ${styles[accent]} ring-2 ring-transparent transition-all duration-300 ${ring[accent]} ${className ?? ''}`}
      aria-hidden="true"
    >
      <Icon size={iconSizes[size]} strokeWidth={2} />
    </span>
  );
}
