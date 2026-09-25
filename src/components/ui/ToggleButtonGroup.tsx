import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: any[]) { return twMerge(clsx(inputs)); }

interface ToggleOption {
  label: string;
  value: string;
  icon?: React.ReactNode;
  /** Greyed out and not selectable; `title` explains why on hover. */
  disabled?: boolean;
  title?: string;
}

interface ToggleButtonGroupProps {
  options: ToggleOption[];
  value: string;
  onChange: (value: string) => void;
  size?: 'sm' | 'md';
}

export function ToggleButtonGroup({ options, value, onChange, size = 'sm' }: ToggleButtonGroupProps) {
  return (
    <div className="flex bg-slate-800 rounded-lg p-0.5 border border-slate-700">
      {options.map(opt => (
        <button key={opt.value}
          onClick={() => { if (!opt.disabled) onChange(opt.value); }}
          disabled={opt.disabled}
          title={opt.title}
          aria-disabled={opt.disabled}
          className={cn(
            "flex items-center gap-1 rounded-md transition-all",
            size === 'sm' ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-xs",
            opt.disabled
              ? "text-slate-500 cursor-not-allowed line-through decoration-slate-600"
              : value === opt.value
                ? "bg-emerald-500/20 text-emerald-400 font-bold"
                : "text-slate-400 hover:text-slate-300"
          )}>
          {opt.icon}
          {opt.label}
        </button>
      ))}
    </div>
  );
}
