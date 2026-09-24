import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: any[]) { return twMerge(clsx(inputs)); }

/**
 * Hover / keyboard-focus tooltip. Pure CSS, no positioning library: the bubble sits
 * below the trigger, centred, and is clipped to a readable width. Used for table
 * column headers and property labels, where the native `title` hint is too slow
 * to appear and too easy to miss.
 */
export function Tooltip({ text, children, className, align = 'center' }: {
  text: string;
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right';
}) {
  return (
    <span className={cn('relative inline-flex group cursor-help', className)} tabIndex={0}>
      {children}
      <span
        role="tooltip"
        className={cn(
          'pointer-events-none absolute top-full z-50 mt-1.5 w-max max-w-[260px] whitespace-pre-line rounded-lg',
          'border border-slate-700 bg-slate-900 px-2.5 py-1.5 shadow-xl',
          'text-left text-[11px] font-normal normal-case leading-snug tracking-normal text-slate-200',
          'opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-visible:opacity-100',
          align === 'center' && 'left-1/2 -translate-x-1/2',
          align === 'left' && 'left-0',
          align === 'right' && 'right-0',
        )}
      >
        {text}
      </span>
    </span>
  );
}
