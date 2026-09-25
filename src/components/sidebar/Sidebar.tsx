import React, { useMemo, useState } from 'react';
import { Search, ChevronLeft, ChevronDown, X } from 'lucide-react';
import { motion, useDragControls } from 'motion/react';
import { DragGrip, dragToClose } from '../ui/DragToClose';
import { DynamicFilterPanel } from './DynamicFilterPanel';
import { APP_VERSION } from '../../version';
import { cn } from '../../utils/cn';
import { getCountryDisplay } from '../../utils/countryUtils';
import type { Simulant, LunarSite, DynamicFilter, FilterProperty } from '../../types';

/** Filters the pane sets directly with chips and ranges; "More filters" holds the rest. */
const QUICK: FilterProperty[] = ['type', 'availability', 'has_chemistry', 'has_mineralogy', 'has_geotechnical', 'bulk_density', 'd50', 'friction_angle', 'cohesion'];
const RANGES: { property: FilterProperty; label: string; step: string }[] = [
  { property: 'bulk_density', label: 'Bulk density (g/cm³)', step: '0.01' },
  { property: 'd50', label: 'D50 (µm)', step: '1' },
  { property: 'friction_angle', label: 'Friction angle (°)', step: '0.1' },
  { property: 'cohesion', label: 'Cohesion (kPa)', step: '0.1' },
];
const DATA_CHIPS: { property: FilterProperty; label: string }[] = [
  { property: 'has_chemistry', label: 'Chemistry' },
  { property: 'has_mineralogy', label: 'Mineralogy' },
  { property: 'has_geotechnical', label: 'Geotechnical' },
];
export const PROGRAMMES = ['Apollo', 'Luna', 'Chang-e', 'Other'] as const;
const PROGRAMME_LABEL: Record<string, string> = { Apollo: 'Apollo', Luna: 'Luna', 'Chang-e': "Chang'e", Other: 'Other' };

interface SidebarProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map' | 'table';
  searchQuery: string;
  onSearchChange: (q: string) => void;
  filters: DynamicFilter[];
  filterOptions: {
    types: string[]; countries: string[]; institutions: string[]; detailedMinerals: string[];
    groupMinerals: string[]; chemicals: string[]; availabilities: string[];
  };
  onAddFilter: (property: FilterProperty) => void;
  onUpdateFilter: (id: string, values: string[]) => void;
  onRemoveFilter: (id: string) => void;
  clearAllFilters: () => void;
  setFacet: (property: FilterProperty, values: string[]) => void;
  facetCounts: (property: FilterProperty, valueOf: (s: Simulant) => string[]) => Map<string, number>;
  countWith: (property: FilterProperty, values: string[]) => number;
  filteredSimulants: Simulant[];
  totalCount: number;
  compareIds: string[];
  onToggleCompare: (id: string) => void;
  selectedSimulantId: string | null;
  onSelectSimulant: (id: string) => void;
  /** Moon: the missions shown (after programme and search), all of them, and the programme chips. */
  lunarSites: LunarSite[];
  allLunarSites: LunarSite[];
  programmes: string[];
  onToggleProgramme: (p: string) => void;
  selectedLunarSiteId: string | null;
  onSelectLunarSite: (id: string) => void;
  onClose: () => void;
}

function Chip({ active, count, onClick, children }: { active: boolean; count?: number; onClick: () => void; children: React.ReactNode; key?: React.Key }) {
  return (
    <button type="button" onClick={onClick} aria-pressed={active}
      className={cn('flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs transition-colors',
        active ? 'bg-emerald-500 border-emerald-500 text-slate-950 font-semibold' : 'border-slate-700 text-slate-300 hover:border-slate-500 hover:text-white',
        count === 0 && !active && 'opacity-50')}>
      {children}{count != null && <span className={active ? 'text-slate-900' : 'text-slate-500'}>{count}</span>}
    </button>
  );
}

/**
 * The "Find" pane (review #5): filtering is its job. On the globe and the map it also lists the
 * results, one line each; in the table it holds only the filters, since the table is the list.
 * On the Moon it becomes "Missions", with programme chips that filter the markers and the table.
 */
export function Sidebar(props: SidebarProps) {
  const drag = useDragControls();
  const [moreOpen, setMoreOpen] = useState(false);
  const valuesOf = (p: FilterProperty) => props.filters.find(f => f.property === p)?.values ?? [];
  const toggleValue = (p: FilterProperty, v: string) => {
    const cur = valuesOf(p);
    props.setFacet(p, cur.includes(v) ? cur.filter(x => x !== v) : [...cur, v]);
  };

  const typeCounts = useMemo(() => props.facetCounts('type', s => s.type ? [s.type] : []), [props.facetCounts]);
  const availabilityCounts = useMemo(() => props.facetCounts('availability', s => s.availability ? [s.availability] : []), [props.facetCounts]);
  // what clicking the chip would leave, under the other filters
  const dataCounts = useMemo(() => Object.fromEntries(DATA_CHIPS.map(c => [c.property, props.countWith(c.property, ['yes'])])), [props.countWith]);
  const byCount = (m: Map<string, number>) => [...m.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const moreFilters = props.filters.filter(f => !QUICK.includes(f.property));
  const activeCount = props.filters.length + (props.searchQuery ? 1 : 0);

  const programmeCounts = useMemo(() => {
    const m = new Map<string, number>();
    for (const s of props.allLunarSites) m.set(s.type, (m.get(s.type) ?? 0) + 1);
    return m;
  }, [props.allLunarSites]);

  const earth = props.planet === 'earth';
  const showList = props.viewMode !== 'table';

  return (
    <motion.div
      initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      {...dragToClose('left', drag, props.onClose)}
      role="complementary" aria-label={earth ? 'Find simulants' : 'Missions'}
      className="absolute left-0 top-14 bottom-0 w-80 max-w-[85vw] bg-slate-900/95 backdrop-blur-xl border-r border-slate-800 z-[50] flex flex-col"
    >
      <DragGrip direction="left" controls={drag} onClose={props.onClose} />

      <div className={cn("p-4 space-y-3 border-b border-slate-800 overflow-y-auto custom-scrollbar", showList ? "max-h-[60%]" : "flex-1")}>
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">{earth ? 'Find simulants' : 'Missions'}</h2>
          <button onClick={props.onClose} aria-label="Close the pane" className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400"><ChevronLeft size={18} /></button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input type="search" aria-label={earth ? 'Search simulants' : 'Search missions'}
            placeholder={earth ? 'Name, producer or country' : 'Mission or site'}
            value={props.searchQuery} onChange={(e) => props.onSearchChange(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl py-2 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50" />
        </div>

        {earth ? (
          <>
            <fieldset>
              <legend className="text-xs text-slate-400 mb-1.5">Type</legend>
              <div className="flex flex-wrap gap-1.5">
                {byCount(typeCounts).map(([v, n]) => <Chip key={v} active={valuesOf('type').includes(v)} count={n} onClick={() => toggleValue('type', v)}>{v}</Chip>)}
              </div>
            </fieldset>
            <fieldset>
              <legend className="text-xs text-slate-400 mb-1.5">Availability</legend>
              <div className="flex flex-wrap gap-1.5">
                {byCount(availabilityCounts).map(([v, n]) => <Chip key={v} active={valuesOf('availability').includes(v)} count={n} onClick={() => toggleValue('availability', v)}>{v}</Chip>)}
              </div>
            </fieldset>
            <fieldset>
              <legend className="text-xs text-slate-400 mb-1.5">Has data</legend>
              <div className="flex flex-wrap gap-1.5">
                {DATA_CHIPS.map(c => {
                  const on = valuesOf(c.property)[0] === 'yes';
                  return <Chip key={c.property} active={on} count={dataCounts[c.property] as number} onClick={() => props.setFacet(c.property, on ? [] : ['yes'])}>{c.label}</Chip>;
                })}
              </div>
            </fieldset>
            <fieldset className="space-y-1.5">
              <legend className="text-xs text-slate-400 mb-1">Ranges</legend>
              {RANGES.map(r => {
                const [min = '', max = ''] = valuesOf(r.property);
                const set = (lo: string, hi: string) => props.setFacet(r.property, lo || hi ? [lo, hi] : []);
                return (
                  <div key={r.property} className="flex items-center gap-1.5 text-xs">
                    <span className="flex-1 text-slate-300">{r.label}</span>
                    <input type="number" inputMode="decimal" step={r.step} value={min} placeholder="min" aria-label={`${r.label} minimum`}
                      onChange={(e) => set(e.target.value, max)} className="w-16 bg-slate-800 border border-slate-700 rounded-md px-1.5 py-1 text-slate-200" />
                    <span className="text-slate-500">–</span>
                    <input type="number" inputMode="decimal" step={r.step} value={max} placeholder="max" aria-label={`${r.label} maximum`}
                      onChange={(e) => set(min, e.target.value)} className="w-16 bg-slate-800 border border-slate-700 rounded-md px-1.5 py-1 text-slate-200" />
                  </div>
                );
              })}
              <p className="text-[11px] text-slate-500">A range leaves out simulants with no value for it.</p>
            </fieldset>
            <div>
              <button onClick={() => setMoreOpen(o => !o)} aria-expanded={moreOpen}
                className="flex items-center gap-1 text-xs text-slate-300 hover:text-white">
                More filters{moreFilters.length > 0 && ` (${moreFilters.length})`}
                <ChevronDown size={14} className={cn('transition-transform', moreOpen && 'rotate-180')} />
              </button>
              {(moreOpen || moreFilters.length > 0) && (
                <div className="mt-2">
                  <DynamicFilterPanel
                    filters={moreFilters}
                    filterOptions={props.filterOptions}
                    onAddFilter={props.onAddFilter}
                    onUpdateFilter={props.onUpdateFilter}
                    onRemoveFilter={props.onRemoveFilter}
                    onClearAll={props.clearAllFilters}
                  />
                </div>
              )}
            </div>
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-300">{props.filteredSimulants.length} of {props.totalCount}</span>
              {activeCount > 0 && <button onClick={props.clearAllFilters} className="flex items-center gap-1 text-slate-400 hover:text-white"><X size={12} />Clear all</button>}
            </div>
          </>
        ) : (
          <>
            <div className="flex flex-wrap gap-1.5" role="group" aria-label="Programme">
              {PROGRAMMES.filter(p => programmeCounts.has(p)).map(p => (
                <Chip key={p} active={props.programmes.includes(p)} count={programmeCounts.get(p)} onClick={() => props.onToggleProgramme(p)}>{PROGRAMME_LABEL[p]}</Chip>
              ))}
            </div>
            <p className="text-xs text-slate-300">{props.lunarSites.length} of {props.allLunarSites.length} missions</p>
          </>
        )}
      </div>

      {showList && (
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {earth ? (
            props.filteredSimulants.length === 0 ? (
              <div className="p-6 text-center text-sm text-slate-400">No simulants match.{activeCount > 0 && <button onClick={props.clearAllFilters} className="block mx-auto mt-2 text-emerald-400 hover:underline">Clear filters</button>}</div>
            ) : (
              <ul>
                {props.filteredSimulants.map(s => {
                  const selected = s.simulant_id === props.selectedSimulantId;
                  return (
                    <li key={s.simulant_id} className={cn('flex items-center gap-2 px-3 border-b border-slate-800/60', selected ? 'bg-emerald-500/10' : 'hover:bg-slate-800/50')}>
                      <input type="checkbox" checked={props.compareIds.includes(s.simulant_id)} onChange={() => props.onToggleCompare(s.simulant_id)}
                        aria-label={`Add ${s.name} to the comparison`} className="accent-emerald-500 cursor-pointer" />
                      <button onClick={() => props.onSelectSimulant(s.simulant_id)} className="flex-1 min-w-0 text-left py-2">
                        <span className={cn('block text-sm font-medium truncate', selected ? 'text-emerald-400' : 'text-slate-200')}>{s.name}</span>
                        <span className="block text-xs text-slate-400 truncate">{[s.type, getCountryDisplay(s.country_code)].filter(Boolean).join(' · ') || '—'}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )
          ) : (
            PROGRAMMES.map(p => {
              const sites = props.lunarSites.filter(s => s.type === p);
              if (sites.length === 0) return null;
              return (
                <div key={p}>
                  <h3 className="px-3 pt-3 pb-1 text-xs font-semibold text-slate-400">{PROGRAMME_LABEL[p]}</h3>
                  <ul>
                    {sites.map(site => {
                      const selected = site.id === props.selectedLunarSiteId;
                      return (
                        <li key={site.id}>
                          <button onClick={() => props.onSelectLunarSite(site.id)}
                            className={cn('w-full flex items-baseline justify-between gap-2 px-3 py-2 text-left border-b border-slate-800/60', selected ? 'bg-amber-500/10' : 'hover:bg-slate-800/50')}>
                            <span className={cn('text-sm font-medium', selected ? 'text-amber-400' : 'text-slate-200')}>{site.mission}</span>
                            <span className="text-xs text-slate-400">{site.date ?? '—'}</span>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              );
            })
          )}
        </div>
      )}

      <div className="mt-auto px-4 py-2 border-t border-slate-800 text-[11px] text-slate-500">{APP_VERSION}</div>
    </motion.div>
  );
}
