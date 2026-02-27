import React, { useState, useRef, useEffect } from 'react';
import { Plus, X } from 'lucide-react';
import { FilterCard } from './FilterCard';
import { FILTER_PROPERTIES } from '../../hooks/useFilters';
import { getCountryDisplay } from '../../utils/countryUtils';
import type { DynamicFilter, FilterProperty } from '../../types';

interface DynamicFilterPanelProps {
  filters: DynamicFilter[];
  filterOptions: {
    types: string[];
    countries: string[];
    institutions: string[];
    detailedMinerals: string[];
    groupMinerals: string[];
    chemicals: string[];
    availabilities: string[];
  };
  onAddFilter: (property: FilterProperty) => void;
  onUpdateFilter: (id: string, values: string[]) => void;
  onRemoveFilter: (id: string) => void;
  onClearAll: () => void;
}

export function DynamicFilterPanel({
  filters, filterOptions, onAddFilter, onUpdateFilter, onRemoveFilter, onClearAll,
}: DynamicFilterPanelProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const getOptionsForFilter = (filter: DynamicFilter): { options?: { label: string; value: string }[]; groups?: { label: string; options: { label: string; value: string }[] }[] } => {
    switch (filter.property) {
      case 'type':
        return { options: filterOptions.types.map(t => ({ label: t, value: t })) };
      case 'country':
        return { options: [
          { label: 'European Union', value: 'EU' },
          ...filterOptions.countries.map(c => ({ label: getCountryDisplay(c), value: c })),
        ]};
      case 'institution':
        return { options: filterOptions.institutions.map(i => ({ label: i, value: i })) };
      case 'availability':
        return { options: filterOptions.availabilities.map(a => ({ label: a, value: a })) };
      case 'mineral':
        return { groups: [
          { label: 'Detailed Minerals', options: filterOptions.detailedMinerals.map(m => ({ label: m, value: m })) },
          { label: 'NASA Mineral Groups', options: filterOptions.groupMinerals.map(m => ({ label: m, value: `group:${m}` })) },
        ]};
      case 'chemical':
        return { options: filterOptions.chemicals.map(c => ({ label: c, value: c })) };
      case 'lunar_ref':
        return { options: (filterOptions as any).lunarRefs?.map((r: string) => ({ label: r, value: r })) || [] };
      default:
        return {};
    }
  };

  return (
    <div className="space-y-2">
      {/* Active filter cards */}
      {filters.map(f => {
        const meta = FILTER_PROPERTIES.find(p => p.property === f.property)!;
        const opts = getOptionsForFilter(f);
        return (
          <FilterCard
            key={f.id}
            filter={f}
            meta={meta}
            options={opts.options}
            groups={opts.groups}
            onUpdate={(values: string[]) => onUpdateFilter(f.id, values)}
            onRemove={() => onRemoveFilter(f.id)}
          />
        );
      })}

      {/* Add Filter button */}
      <div ref={menuRef} className="relative">
        <button onClick={() => setMenuOpen(!menuOpen)}
          className="w-full flex items-center justify-center gap-1.5 py-2 bg-slate-800/40 hover:bg-slate-800/70 border border-dashed border-slate-700/50 hover:border-slate-600 rounded-xl text-xs text-slate-500 hover:text-slate-300 transition-all">
          <Plus size={14} />
          Add Filter
        </button>

        {menuOpen && (
          <div className="absolute bottom-full left-0 right-0 mb-1 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-[100] max-h-60 overflow-y-auto">
            {FILTER_PROPERTIES.map(p => (
              <button key={p.property}
                onClick={() => { onAddFilter(p.property); setMenuOpen(false); }}
                className="w-full text-left px-3 py-2 text-xs text-slate-300 hover:bg-slate-700/50 transition-colors flex items-center justify-between">
                <span>{p.label}</span>
                <span className="text-[10px] text-slate-600 uppercase">{p.type}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Clear All */}
      {filters.length > 0 && (
        <button onClick={onClearAll}
          className="w-full flex items-center justify-center gap-2 py-2 bg-orange-600/20 hover:bg-orange-600/30 border border-orange-500/30 text-orange-400 rounded-lg text-xs font-bold transition-all">
          <X size={12} />
          Clear All Filters
        </button>
      )}
    </div>
  );
}
