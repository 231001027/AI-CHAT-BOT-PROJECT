import type { HTMLAttributes, ReactNode } from 'react';
import { motion } from 'framer-motion';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  hover?: boolean;
  as?: 'div' | 'article' | 'section';
}

export function Card({ children, hover = false, className = '', ...rest }: CardProps) {
  return (
    <motion.div
      whileHover={hover ? { y: -6 } : undefined}
      transition={{ type: 'spring', stiffness: 300, damping: 22 }}
      className={`card ${hover ? 'hover:shadow-card-hover' : ''} ${className}`}
      {...(rest as Record<string, unknown>)}
    >
      {children}
    </motion.div>
  );
}
