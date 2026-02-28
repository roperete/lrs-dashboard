import React, { useState, useRef, useEffect } from 'react';
import { X, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';
import { getCountryDisplay } from '../../utils/countryUtils';
import type { DynamicFilter, FilterPropertyMeta } from '../../types';

interface FilterOption {
  label: string;
  value: string;
}

interface FilterGroup {
  label: string;
  options: FilterOption[];
}

interface FilterCardProps {
  key?: React.Key;
  filter: DynamicFilter;
  meta: FilterPropertyMeta;
  options?: FilterOption[];
  groups?: FilterGroup[];
  onUpdate: (values: string[]) => void;
  onRemove: () => void;
}

function CategoricalInput({ filter, options, groups, onUpdate }: {
  filter: DynamicFilter; options?: FilterOption[]; groups?: FilterGroup[]; onUpdate: (v: string[]) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent | TouchEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    document.addEventListener('touchstart', handler);
    return () => {
      document.removeEventListener('mousedown', handler);
      document.removeEventListener('touchstart', handler);
    };
  }, []);

  const allOptions = groups ? groups.flatMap(g => g.options) : options || [];

  const toggle = (value: string) => {
    onUpdate(
      filter.values.includes(value)
        ? filter.values.filter(v => v !== value)
        : [...filter.values, value]
    );
  };

  return (
    <div ref={ref} className="relative">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between bg-slate-800/60 border border-slate-700/50 rounded-lg py-1.5 px-2.5 text-xs text-slate-300 hover:border-slate-600 transition-colors">
        <span className="truncate">
          {filter.values.length === 0 ? 'Select...' : `${filter.values.length} selected`}
        </span>
        <ChevronDown size={12} className={cn("transition-transform ml-1", open && "rotate-180")} />
      </button>

      {open && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-[100] max-h-[40vh] md:max-h-48 overflow-y-auto overflow-x-hidden">
          <div className="flex items-center gap-2 p-1.5 border-b border-slate-700">
            <button onClick={() => onUpdate(allOptions.map(o => o.value))}
              className="text-[10px] px-1.5 py-0.5 bg-slate-700 hover:bg-slate-600 rounded text-emerald-400 font-bold">All</button>
            <button onClick={() => onUpdate([])}
              className="text-[10px] px-1.5 py-0.5 bg-slate-700 hover:bg-slate-600 rounded text-slate-400 font-bold">None</button>
          </div>
          {groups ? (
            groups.map(group => (
              <div key={group.label}>
                <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-800/80 sticky top-0">
                  {group.label}
                </div>
                {group.options.map(opt => (
                  <label key={opt.value} className="flex items-center gap-2 px-2.5 py-1 hover:bg-slate-700/50 cursor-pointer text-xs">
                    <input type="checkbox" checked={filter.values.includes(opt.value)} onChange={() => toggle(opt.value)} className="accent-emerald-500 rounded" />
                    <span className="text-slate-300 truncate">{opt.label}</span>
                  </label>
                ))}
              </div>
            ))
          ) : (
            allOptions.map(opt => (
              <label key={opt.value} className="flex items-center gap-2 px-2.5 py-1 hover:bg-slate-700/50 cursor-pointer text-xs">
                <input type="checkbox" checked={filter.values.includes(opt.value)} onChange={() => toggle(opt.value)} className="accent-emerald-500 rounded" />
                <span className="text-slate-300 truncate">{opt.label}</span>
              </label>
            ))
          )}
        </div>
      )}
    </div>
  );
}

function BooleanInput({ filter, onUpdate }: { filter: DynamicFilter; onUpdate: (v: string[]) => void }) {
  const val = filter.values[0] || '';
  return (
    <div className="flex gap-1">
      {['yes', 'no'].map(v => (
        <button key={v} onClick={() => onUpdate(val === v ? [] : [v])}
          className={cn(
            "flex-1 py-1 px-2 rounded-lg text-xs font-medium transition-all",
            val === v ? "bg-emerald-500 text-slate-950" : "bg-slate-800/60 text-slate-400 hover:text-white border border-slate-700/50",
          )}>
          {v === 'yes' ? 'Yes' : 'No'}
        </button>
      ))}
    </div>
  );
}

function RangeInput({ filter, onUpdate }: { filter: DynamicFilter; onUpdate: (v: string[]) => void }) {
  const [min, max] = [filter.values[0] || '', filter.values[1] || ''];
  return (
    <div className="flex gap-1.5 items-center">
      <input type="number" placeholder="Min" value={min}
        onChange={e => onUpdate([e.target.value, max])}
        className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg py-1.5 px-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/50" />
      <span className="text-slate-600 text-xs">\u2013</span>
      <input type="number" placeholder="Max" value={max}
        onChange={e => onUpdate([min, e.target.value])}
        className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg py-1.5 px-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/50" />
    </div>
  );
}

function TextInput({ filter, onUpdate }: { filter: DynamicFilter; onUpdate: (v: string[]) => void }) {
  return (
    <input type="text" placeholder="Search..." value={filter.values[0] || ''}
      onChange={e => onUpdate([e.target.value])}
      className="w-full bg-slate-800/60 border border-slate-700/50 rounded-lg py-1.5 px-2 text-xs text-slate-300 focus:outline-none focus:ring-1 focus:ring-emerald-500/50" />
  );
}

export function FilterCard({ filter, meta, options, groups, onUpdate, onRemove }: FilterCardProps) {
  return (
    <div className="bg-slate-800/30 border border-slate-700/40 rounded-xl p-2.5 space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{meta.label}</span>
        <button onClick={onRemove} className="p-0.5 hover:bg-slate-700 rounded text-slate-600 hover:text-slate-400 transition-colors">
          <X size={12} />
        </button>
      </div>
      {meta.type === 'categorical' && <CategoricalInput filter={filter} options={options} groups={groups} onUpdate={onUpdate} />}
      {meta.type === 'boolean' && <BooleanInput filter={filter} onUpdate={onUpdate} />}
      {meta.type === 'range' && <RangeInput filter={filter} onUpdate={onUpdate} />}
      {meta.type === 'text' && <TextInput filter={filter} onUpdate={onUpdate} />}
    </div>
  );
}
