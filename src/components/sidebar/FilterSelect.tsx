import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, X } from 'lucide-react';

interface FilterOption {
  label: string;
  value: string;
}

interface FilterGroup {
  label: string;
  options: FilterOption[];
}

interface FilterSelectProps {
  label: string;
  selected: string[];
  options?: FilterOption[];
  groups?: FilterGroup[];
  onChange: (values: string[]) => void;
}

export function FilterSelect({ label, selected, options, groups, onChange }: FilterSelectProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const allOptions = groups
    ? groups.flatMap(g => g.options)
    : options || [];

  const toggleValue = (value: string) => {
    onChange(
      selected.includes(value)
        ? selected.filter(v => v !== value)
        : [...selected, value]
    );
  };

  const selectAll = () => onChange(allOptions.map(o => o.value));
  const deselectAll = () => onChange([]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between bg-slate-800 border border-slate-700 rounded-lg py-2 px-3 text-sm text-slate-200 hover:border-slate-600 transition-colors"
      >
        <span className="truncate">
          {selected.length === 0 ? label : `${label} (${selected.length})`}
        </span>
        <ChevronDown size={14} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-[100] max-h-60 overflow-y-auto">
          <div className="flex items-center gap-2 p-2 border-b border-slate-700">
            <button onClick={selectAll} className="text-[10px] px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-emerald-400 font-bold">
              All
            </button>
            <button onClick={deselectAll} className="text-[10px] px-2 py-1 bg-slate-700 hover:bg-slate-600 rounded text-slate-400 font-bold">
              None
            </button>
            {selected.length > 0 && (
              <span className="text-[10px] text-slate-500 ml-auto">{selected.length} selected</span>
            )}
          </div>

          {groups ? (
            groups.map(group => (
              <div key={group.label}>
                <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 bg-slate-800/80 sticky top-0">
                  {group.label}
                </div>
                {group.options.map(opt => (
                  <label key={opt.value}
                    className="flex items-center gap-2 px-3 py-1.5 hover:bg-slate-700/50 cursor-pointer text-sm">
                    <input
                      type="checkbox"
                      checked={selected.includes(opt.value)}
                      onChange={() => toggleValue(opt.value)}
                      className="accent-emerald-500 rounded"
                    />
                    <span className="text-slate-300 truncate">{opt.label}</span>
                  </label>
                ))}
              </div>
            ))
          ) : (
            allOptions.map(opt => (
              <label key={opt.value}
                className="flex items-center gap-2 px-3 py-1.5 hover:bg-slate-700/50 cursor-pointer text-sm">
                <input
                  type="checkbox"
                  checked={selected.includes(opt.value)}
                  onChange={() => toggleValue(opt.value)}
                  className="accent-emerald-500 rounded"
                />
                <span className="text-slate-300 truncate">{opt.label}</span>
              </label>
            ))
          )}
        </div>
      )}
    </div>
  );
}
