import React, { useState, useMemo, useRef, useCallback } from 'react';
import { ChevronUp, ChevronDown, Check } from 'lucide-react';

import { cn } from '../../utils/cn';
import { Tooltip } from '../ui/Tooltip';
import { RefSup } from '../ui/RefSup';
import { referenceHoverLabel } from '../../utils/references';
import { getCountryDisplay } from '../../utils/countryUtils';
import { sortSimulants, type SortKey, type SortDir } from '../../utils/sortSimulants';
import type { PaneSection } from '../../hooks/usePanelState';
import type { Simulant, ChemicalComposition, Composition, Reference, PropertySource } from '../../types';

const DASH = '—';

/** One-line explanation of each column, shown on hover over the header. */
const COLUMN_HELP: Record<SortKey, string> = {
  name: 'Product name as the producer writes it.',
  type: 'Lunar terrain the simulant is meant to stand in for: highlands, mare, or a general or engineering material.',
  country: 'Country of the producing institution.',
  institution: 'Organisation that produces, or produced, the simulant.',
  availability: 'Whether the product can currently be obtained, as last recorded. Not yet audited.',
  lunar_sample_reference: 'The lunar material the producer says the simulant replicates, in the producer\'s own words.',
  year: 'Year first produced or released, as recorded. Not yet audited; the sheets do not state it.',
  specific_gravity: 'Grain density relative to water. Cleared wherever the value only repeated the bulk density.',
  bulk_density: 'Mass per unit volume, pore space included, in g/cm³, as the source states it: sources differ in packing (loose, compacted, optimal); the citation says which.',
  d50: 'Median particle size in micrometres: half the grains, by mass, are finer than this.',
  friction_angle: 'Internal angle of friction from shear testing, in degrees. Governs slope stability and bearing capacity.',
  cohesion: 'Shear strength at zero normal stress, in kPa. How much the grains hold together.',
  has_chemistry: 'Oxide chemistry on record, each value cited. Click the mark to open it in the pane.',
  has_mineralogy: 'Mineral or component composition on record, each value cited. Click the mark to open it in the pane.',
  references: 'Documents on record for this simulant, and how many a reader confirmed name it. Click to open them in the pane.',
};

/** Display a sparse field, falling back to an em-dash when empty. */
const show = (v: unknown): string => (v == null || v === '' ? DASH : String(v));

interface SimulantTableProps {
  simulants: Simulant[];
  selectedSimulantId: string | null;
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  compositionBySimulant: Map<string, Composition[]>;
  referencesBySimulant: Map<string, Reference[]>;
  /** property_sources rows keyed by simulant then field, for the citation superscripts. */
  propertySourcesBySimulant?: Map<string, Map<string, PropertySource>>;
  /** Number of a reference within its simulant's list; see utils/references.ts. */
  refNumber?: (simulantId: string, referenceId: string) => number | undefined;
  /** Open the simulant's pane, at a section when a cell asks for one. */
  onSelectSimulant: (id: string, section?: PaneSection) => void;
  /** The compare tray: a row's checkbox adds or removes it. */
  compareIds: string[];
  onToggleCompare: (id: string) => void;
  onClearFilters?: () => void;
}

/**
 * The table. The right pane is the one place a simulant's details are shown (review #4): a row
 * click, or Enter on a focused row, opens it; ↑/↓ move the selection and the pane follows; the
 * data marks open it at the section they stand for. Checkboxes only feed the compare tray.
 */
export function SimulantTable({
  simulants, selectedSimulantId,
  chemicalBySimulant, compositionBySimulant, referencesBySimulant,
  propertySourcesBySimulant, refNumber,
  onSelectSimulant, compareIds, onToggleCompare, onClearFilters,
}: SimulantTableProps) {
  /** A scalar cell with its citation, the same mark the right pane shows for the value. */
  const scalarCell = (s: Simulant, field: keyof Simulant) => {
    const v = s[field];
    const source = propertySourcesBySimulant?.get(s.simulant_id)?.get(field);
    const n = source ? refNumber?.(s.simulant_id, source.reference_id) : undefined;
    return (
      <td className="py-2 px-3 text-right text-slate-300 font-mono whitespace-nowrap">
        {show(v)}
        {v != null && v !== '' && source && n != null && (
          <RefSup n={n} location={source.location} quote={source.quote} align="right"
            source={referenceHoverLabel(referencesBySimulant.get(s.simulant_id)?.find(r => r.reference_id === source.reference_id))} />
        )}
      </td>
    );
  };
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const bodyRef = useRef<HTMLTableSectionElement>(null);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const sorted = useMemo(
    () => sortSimulants(simulants, sortKey, sortDir, { chemicalBySimulant, compositionBySimulant, referencesBySimulant }),
    [simulants, sortKey, sortDir, chemicalBySimulant, compositionBySimulant, referencesBySimulant]);

  const compare = useMemo(() => new Set(compareIds), [compareIds]);

  /** ↑/↓ move the selection; Enter or Space opens the focused row. */
  const onRowKey = useCallback((e: React.KeyboardEvent<HTMLTableRowElement>, index: number) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelectSimulant(sorted[index].simulant_id); return; }
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    e.preventDefault();
    const next = Math.min(sorted.length - 1, Math.max(0, index + (e.key === 'ArrowDown' ? 1 : -1)));
    const row = bodyRef.current?.querySelectorAll<HTMLTableRowElement>('tr[data-row]')[next];
    row?.focus();
    onSelectSimulant(sorted[next].simulant_id);
  }, [sorted, onSelectSimulant]);

  const headBase = "py-2 px-3 text-xs font-semibold whitespace-nowrap sticky top-0 bg-slate-900 z-20";
  const TH = ({ col, label, align = 'left', className }: { col: SortKey; label: string; align?: 'left' | 'right' | 'center'; className?: string }) => (
    <th scope="col" aria-sort={sortKey === col ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none'}
      className={cn(headBase, align === 'right' && 'text-right', align === 'center' && 'text-center', className)}>
      <Tooltip text={COLUMN_HELP[col]} align={align === 'right' ? 'right' : align === 'center' ? 'center' : 'left'}>
        <button type="button" onClick={() => toggleSort(col)}
          className={cn("inline-flex items-center gap-1 hover:text-white", sortKey === col ? 'text-emerald-400' : 'text-slate-400')}>
          {label}
          {sortKey === col ? (sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />) : <span className="w-3.5" />}
        </button>
      </Tooltip>
    </th>
  );
  // The checkbox and Name columns stay put while the table scrolls sideways.
  const stickyBox = "sticky left-0 z-10";
  const stickyName = "sticky left-10 z-10";

  return (
    <div className="h-full overflow-auto scrollbar-thin relative">
      {/* Phones: a list, not 16 columns scrolled sideways (review #23) */}
      <ul className="sm:hidden divide-y divide-slate-800">
        {sorted.map(s => {
          const isSelected = s.simulant_id === selectedSimulantId;
          const key = [['ρ', s.bulk_density, 'g/cm³'], ['D50', s.particle_size_d50, 'µm'], ['φ', s.friction_angle, '°']]
            .filter(([, v]) => v != null && v !== '').map(([l, v, u]) => `${l} ${v} ${u}`).join(' · ');
          return (
            <li key={s.simulant_id} className={cn("flex items-center gap-3 px-3 py-2.5", isSelected && "bg-emerald-950")}>
              <input type="checkbox" checked={compare.has(s.simulant_id)} onChange={() => onToggleCompare(s.simulant_id)}
                aria-label={`Add ${s.name} to the comparison`} className="accent-emerald-500 w-5 h-5" />
              <button onClick={() => onSelectSimulant(s.simulant_id)} className="flex-1 min-w-0 text-left">
                <span className={cn("block text-sm font-medium", isSelected ? "text-emerald-400" : "text-slate-200")}>{s.name}</span>
                <span className="block text-xs text-slate-400 truncate">{[s.type, getCountryDisplay(s.country_code)].filter(Boolean).join(' · ') || DASH}</span>
                {key && <span className="block text-xs text-slate-300 font-mono truncate">{key}</span>}
              </button>
              <span className="text-[11px] text-slate-400 whitespace-nowrap">
                {chemicalBySimulant.has(s.simulant_id) ? 'Chem ' : ''}{compositionBySimulant.has(s.simulant_id) ? 'Min' : ''}
              </span>
            </li>
          );
        })}
      </ul>
      <table className="hidden sm:table w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th scope="col" className={cn(headBase, "left-0 z-30 w-10 px-2")}><span className="sr-only">Compare</span></th>
            <TH col="name" label="Name" className="left-10 z-30" />
            <TH col="type" label="Type" />
            <TH col="country" label="Country" />
            <TH col="institution" label="Institution" />
            <TH col="availability" label="Availability" />
            <TH col="lunar_sample_reference" label="Lunar ref." />
            <TH col="year" label="Year" align="right" />
            <TH col="specific_gravity" label="Spec. grav." align="right" />
            <TH col="bulk_density" label="Bulk dens. (g/cm³)" align="right" />
            <TH col="d50" label="D50 (µm)" align="right" />
            <TH col="friction_angle" label="Friction (°)" align="right" />
            <TH col="cohesion" label="Cohesion (kPa)" align="right" />
            <TH col="has_chemistry" label="Chem." align="center" />
            <TH col="has_mineralogy" label="Miner." align="center" />
            <TH col="references" label="References" align="right" />
          </tr>
        </thead>
        <tbody ref={bodyRef}>
          {sorted.map((s, i) => {
            const isSelected = s.simulant_id === selectedSimulantId;
            const inTray = compare.has(s.simulant_id);
            const refs = referencesBySimulant.get(s.simulant_id) || [];
            const named = refs.filter(r => r.names_simulant === 1).length;
            const rowBg = isSelected ? "bg-emerald-950" : i % 2 === 0 ? "bg-slate-900" : "bg-[#0d1424]";
            const dataMark = (has: boolean, what: string) => has
              ? <button type="button" onClick={(e) => { e.stopPropagation(); onSelectSimulant(s.simulant_id, 'composition'); }}
                  aria-label={`Open ${s.name}'s ${what} in the pane`} className="text-emerald-400 hover:text-emerald-300">
                  <Check size={16} className="inline" />
                </button>
              : <span className="text-slate-500">{DASH}</span>;
            return (
              <tr key={s.simulant_id} data-row tabIndex={0} aria-selected={isSelected}
                onClick={() => onSelectSimulant(s.simulant_id)} onKeyDown={(e) => onRowKey(e, i)}
                className={cn("group cursor-pointer border-b border-slate-800/50 outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-emerald-500",
                  rowBg, "hover:brightness-125")}>
                <td className={cn("py-2 px-2 text-center", stickyBox, rowBg)}>
                  <input type="checkbox" checked={inTray} aria-label={`Add ${s.name} to the comparison`}
                    onChange={() => onToggleCompare(s.simulant_id)} onClick={(e) => e.stopPropagation()}
                    className="accent-emerald-500 cursor-pointer" />
                </td>
                <td className={cn("py-2 px-3 font-medium whitespace-nowrap", stickyName, rowBg, isSelected ? "text-emerald-400" : "text-slate-200")}>{s.name}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.type || DASH}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{getCountryDisplay(s.country_code) || DASH}</td>
                <td className="py-2 px-3 text-slate-400 max-w-[200px] truncate">{s.institution || DASH}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.availability || DASH}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.lunar_sample_reference || DASH}</td>
                <td className="py-2 px-3 text-right text-slate-300 font-mono whitespace-nowrap">{typeof s.release_date === 'number' ? s.release_date : DASH}</td>
                {scalarCell(s, 'specific_gravity')}
                {scalarCell(s, 'bulk_density')}
                {scalarCell(s, 'particle_size_d50')}
                {scalarCell(s, 'friction_angle')}
                {scalarCell(s, 'cohesion')}
                <td className="py-2 px-3 text-center">{dataMark(chemicalBySimulant.has(s.simulant_id), 'chemistry')}</td>
                <td className="py-2 px-3 text-center">{dataMark(compositionBySimulant.has(s.simulant_id), 'mineralogy')}</td>
                <td className="py-2 px-3 text-right whitespace-nowrap">
                  {refs.length > 0
                    ? <button type="button" onClick={(e) => { e.stopPropagation(); onSelectSimulant(s.simulant_id, 'references'); }}
                        aria-label={`Open ${s.name}'s references in the pane`} className="text-slate-300 hover:text-white">
                        {refs.length} <span className="text-slate-400">· {named} named</span>
                      </button>
                    : <span className="text-slate-500">{DASH}</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {sorted.length === 0 && (
        <div className="flex flex-col items-center justify-center gap-3 h-40 text-slate-400 text-sm">
          No simulants match the current filters.
          {onClearFilters && (
            <button onClick={onClearFilters} className="px-3 py-1.5 rounded-lg border border-slate-600 text-slate-200 hover:bg-slate-800">Clear filters</button>
          )}
        </div>
      )}
    </div>
  );
}
