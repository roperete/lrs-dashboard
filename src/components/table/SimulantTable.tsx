import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Check, ArrowRightLeft, Download } from 'lucide-react';

import { cn } from '../../utils/cn';
import { getCountryDisplay } from '../../utils/countryUtils';
import type { Simulant, ChemicalComposition, Composition, Reference } from '../../types';

type SortDir = 'asc' | 'desc';
type SortKey = 'name' | 'type' | 'country' | 'institution' | 'availability' | 'lunar_sample_reference' | 'year' | 'has_chemistry' | 'has_mineralogy' | 'reference';

const DASH = '\u2014';

interface SimulantTableProps {
  simulants: Simulant[];
  selectedSimulantId: string | null;
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  compositionBySimulant: Map<string, Composition[]>;
  referencesBySimulant: Map<string, Reference[]>;
  onSelectSimulant: (id: string) => void;
  onCompareSelected?: (id1: string, id2: string) => void;
  onExportSelected?: (simulants: Simulant[]) => void;
}

function getFirstReference(id: string, referencesBySimulant: Map<string, Reference[]>): string {
  const refs = referencesBySimulant.get(id);
  if (!refs || refs.length === 0) return '';
  return refs[0].reference_text || '';
}

export function SimulantTable({
  simulants, selectedSimulantId,
  chemicalBySimulant, compositionBySimulant, referencesBySimulant,
  onSelectSimulant, onCompareSelected, onExportSelected,
}: SimulantTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');
  const [checkedIds, setCheckedIds] = useState<Set<string>>(new Set());
  const [expandedRefId, setExpandedRefId] = useState<string | null>(null);

  const toggleChecked = (id: string) => {
    setCheckedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };
  const toggleAll = () => {
    if (checkedIds.size === simulants.length) setCheckedIds(new Set());
    else setCheckedIds(new Set(simulants.map(s => s.simulant_id)));
  };

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sorted = useMemo(() => {
    const arr = [...simulants];
    const dir = sortDir === 'asc' ? 1 : -1;

    arr.sort((a, b) => {
      let va: string | number | boolean | null;
      let vb: string | number | boolean | null;

      switch (sortKey) {
        case 'name': va = a.name.toLowerCase(); vb = b.name.toLowerCase(); break;
        case 'type': va = (a.type || '').toLowerCase(); vb = (b.type || '').toLowerCase(); break;
        case 'country': va = getCountryDisplay(a.country_code).toLowerCase(); vb = getCountryDisplay(b.country_code).toLowerCase(); break;
        case 'institution': va = (a.institution || '').toLowerCase(); vb = (b.institution || '').toLowerCase(); break;
        case 'availability': va = (a.availability || '').toLowerCase(); vb = (b.availability || '').toLowerCase(); break;
        case 'lunar_sample_reference': va = (a.lunar_sample_reference || '').toLowerCase(); vb = (b.lunar_sample_reference || '').toLowerCase(); break;
        case 'year': va = typeof a.release_date === 'number' ? a.release_date : null; vb = typeof b.release_date === 'number' ? b.release_date : null; break;
        case 'has_chemistry': va = chemicalBySimulant.has(a.simulant_id) ? 1 : 0; vb = chemicalBySimulant.has(b.simulant_id) ? 1 : 0; break;
        case 'has_mineralogy': va = compositionBySimulant.has(a.simulant_id) ? 1 : 0; vb = compositionBySimulant.has(b.simulant_id) ? 1 : 0; break;
        case 'reference': va = getFirstReference(a.simulant_id, referencesBySimulant).toLowerCase() || null; vb = getFirstReference(b.simulant_id, referencesBySimulant).toLowerCase() || null; break;
        default: return 0;
      }

      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;

      if (typeof va === 'string' && typeof vb === 'string') {
        return va.localeCompare(vb) * dir;
      }
      return ((va as number) - (vb as number)) * dir;
    });

    return arr;
  }, [simulants, sortKey, sortDir, chemicalBySimulant, compositionBySimulant, referencesBySimulant]);

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <span className="w-4" />;
    return sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  const TH = ({ col, label, align = 'left' }: { col: SortKey; label: string; align?: 'left' | 'right' | 'center' }) => (
    <th
      onClick={() => toggleSort(col)}
      className={cn(
        "py-2.5 px-3 text-xs font-bold text-slate-500 uppercase tracking-wider cursor-pointer select-none hover:text-slate-300 transition-colors whitespace-nowrap sticky top-0 bg-slate-900/95 backdrop-blur-sm z-10",
        align === 'right' && 'text-right',
        align === 'center' && 'text-center',
        sortKey === col && 'text-emerald-400',
      )}
    >
      <span className={cn("inline-flex items-center gap-1", align === 'right' && 'justify-end', align === 'center' && 'justify-center')}>
        {label}<SortIcon col={col} />
      </span>
    </th>
  );

  return (
    <div className="h-full overflow-auto scrollbar-thin relative">
      {checkedIds.size > 0 && (
        <div className="sticky top-0 z-20 flex items-center gap-3 px-4 py-2 bg-emerald-500/10 border-b border-emerald-500/30 backdrop-blur-sm">
          <span className="text-xs font-medium text-emerald-400">{checkedIds.size} selected</span>
          {checkedIds.size === 2 && onCompareSelected && (
            <button
              onClick={() => {
                const ids = Array.from(checkedIds);
                onCompareSelected(ids[0], ids[1]);
              }}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 rounded-lg text-xs text-blue-300 transition-colors"
            >
              <ArrowRightLeft size={12} />Compare
            </button>
          )}
          {onExportSelected && (
            <button
              onClick={() => onExportSelected(simulants.filter(s => checkedIds.has(s.simulant_id)))}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 rounded-lg text-xs text-emerald-300 transition-colors"
            >
              <Download size={12} />Export Selected
            </button>
          )}
          <button onClick={() => setCheckedIds(new Set())} className="text-xs text-slate-500 hover:text-slate-300 ml-auto">Clear</button>
        </div>
      )}
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-slate-700/50">
            <th className="py-2.5 px-2 text-center sticky top-0 bg-slate-900/95 backdrop-blur-sm z-10 w-8">
              <input type="checkbox" checked={checkedIds.size === simulants.length && simulants.length > 0} onChange={toggleAll}
                className="accent-emerald-500 cursor-pointer" />
            </th>
            <TH col="name" label="Name" />
            <TH col="type" label="Type" />
            <TH col="country" label="Country" />
            <TH col="institution" label="Institution" />
            <TH col="availability" label="Availability" />
            <TH col="lunar_sample_reference" label="Lunar Ref" />
            <TH col="year" label="Year" align="right" />
            <TH col="has_chemistry" label="Chem" align="center" />
            <TH col="has_mineralogy" label="Miner" align="center" />
            <TH col="reference" label="Reference" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((s, i) => {
            const isSelected = s.simulant_id === selectedSimulantId;
            const isChecked = checkedIds.has(s.simulant_id);
            const ref = getFirstReference(s.simulant_id, referencesBySimulant);
            return (
              <React.Fragment key={s.simulant_id}>
                <tr
                  onClick={() => onSelectSimulant(s.simulant_id)}
                  className={cn(
                    "cursor-pointer transition-colors border-b border-slate-800/50",
                    isSelected
                      ? "bg-emerald-500/15 hover:bg-emerald-500/20"
                      : isChecked
                        ? "bg-blue-500/10 hover:bg-blue-500/15"
                        : i % 2 === 0
                          ? "bg-slate-900/40 hover:bg-slate-800/60"
                          : "bg-slate-900/20 hover:bg-slate-800/60",
                  )}
                >
                  <td className="py-2 px-2 text-center">
                    <input type="checkbox" checked={checkedIds.has(s.simulant_id)}
                      onChange={(e) => { e.stopPropagation(); toggleChecked(s.simulant_id); }}
                      onClick={(e) => e.stopPropagation()}
                      className="accent-emerald-500 cursor-pointer" />
                  </td>
                  <td className={cn("py-2 px-3 font-medium whitespace-nowrap", isSelected ? "text-emerald-400" : "text-slate-200")}>{s.name}</td>
                  <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.type || DASH}</td>
                  <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{getCountryDisplay(s.country_code)}</td>
                  <td className="py-2 px-3 text-slate-400 max-w-[200px] truncate">{s.institution || DASH}</td>
                  <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.availability || DASH}</td>
                  <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.lunar_sample_reference || DASH}</td>
                  <td className="py-2 px-3 text-right text-slate-300 font-mono whitespace-nowrap">{typeof s.release_date === 'number' ? s.release_date : DASH}</td>
                  <td className="py-2 px-3 text-center">
                    {chemicalBySimulant.has(s.simulant_id)
                      ? <Check size={16} className="inline text-emerald-400" />
                      : <span className="text-slate-600">{DASH}</span>
                    }
                  </td>
                  <td className="py-2 px-3 text-center">
                    {compositionBySimulant.has(s.simulant_id)
                      ? <Check size={16} className="inline text-emerald-400" />
                      : <span className="text-slate-600">{DASH}</span>
                    }
                  </td>
                  <td className="py-2 px-3 text-slate-400 max-w-[300px] truncate cursor-pointer hover:text-slate-200 transition-colors"
                    title={ref ? 'Click to expand' : undefined}
                    onClick={(e) => { e.stopPropagation(); if (ref) setExpandedRefId(expandedRefId === s.simulant_id ? null : s.simulant_id); }}>
                    {ref || DASH}
                  </td>
                </tr>
                {expandedRefId === s.simulant_id && ref && (
                  <tr className="bg-slate-800/30">
                    <td colSpan={11} className="px-6 py-3">
                      <p className="text-xs text-slate-300 leading-relaxed whitespace-normal">{ref}</p>
                      {(referencesBySimulant.get(s.simulant_id)?.length || 0) > 1 && (
                        <div className="mt-2 space-y-1">
                          {referencesBySimulant.get(s.simulant_id)!.slice(1).map((r, idx) => (
                            <p key={idx} className="text-xs text-slate-400 leading-relaxed whitespace-normal">{r.reference_text}</p>
                          ))}
                        </div>
                      )}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
          })}
        </tbody>
      </table>
      {sorted.length === 0 && (
        <div className="flex items-center justify-center h-40 text-slate-500 text-sm">
          No simulants match the current filters.
        </div>
      )}
    </div>
  );
}
