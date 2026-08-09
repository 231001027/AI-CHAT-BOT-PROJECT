import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-60',
  {
    variants: {
      variant: {
        default: 'bg-brand-500 text-white shadow-soft hover:bg-brand-600',
        primary: 'bg-brand-500 text-white shadow-soft hover:bg-brand-600',
        secondary:
          'bg-white text-brand-700 border border-brand-100 hover:border-brand-300 hover:bg-brand-50 shadow-soft',
        outline: 'border border-slate-200 bg-white hover:bg-slate-50 text-slate-800',
        ghost: 'bg-transparent text-slate-700 hover:bg-slate-100',
        destructive: 'bg-red-600 text-white hover:bg-red-700',
        link: 'text-brand-600 underline-offset-4 hover:underline',
      },
      size: {
        default: 'px-5 py-3',
        sm: 'px-4 py-2 text-xs',
        md: 'px-5 py-3 text-sm',
        lg: 'px-7 py-4 text-base',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : 'button';
    return (
      <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
    );
  },
);
Button.displayName = 'Button';

type LinkButtonProps = {
  to: string;
  children: React.ReactNode;
  className?: string;
  variant?: 'primary' | 'secondary' | 'ghost' | 'default' | 'outline';
  size?: 'sm' | 'md' | 'lg' | 'default';
};

function LinkButton({
  to,
  children,
  className,
  variant = 'primary',
  size = 'md',
}: LinkButtonProps) {
  return (
    <Link to={to} className={cn(buttonVariants({ variant, size, className }))}>
      {children}
    </Link>
  );
}

export { Button, LinkButton, buttonVariants };
