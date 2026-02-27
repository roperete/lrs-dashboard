import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';
import { getCountryDisplay } from '../../utils/countryUtils';
import type { Simulant, ChemicalComposition, PhysicalProperties } from '../../types';

type SortDir = 'asc' | 'desc';
type SortKey = 'name' | 'type' | 'country' | 'institution' | 'availability' | 'lunar_sample_reference' | 'year' | 'sio2' | 'bulk_density' | 'cohesion';

interface SimulantTableProps {
  simulants: Simulant[];
  selectedSimulantId: string | null;
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  physicalPropsBySimulant: Map<string, PhysicalProperties>;
  onSelectSimulant: (id: string) => void;
}

function getSiO2(id: string, chemicalBySimulant: Map<string, ChemicalComposition[]>): number | null {
  const chems = chemicalBySimulant.get(id);
  if (!chems) return null;
  const sio2 = chems.find(c => c.component_name.toLowerCase() === 'sio2');
  return sio2 ? sio2.value_wt_pct : null;
}

function getBulkDensity(id: string, physicalPropsBySimulant: Map<string, PhysicalProperties>): number | null {
  const props = physicalPropsBySimulant.get(id);
  if (!props || props.bulk_density == null) return null;
  return typeof props.bulk_density === 'number' ? props.bulk_density : null;
}

function getCohesion(id: string, physicalPropsBySimulant: Map<string, PhysicalProperties>): number | null {
  const props = physicalPropsBySimulant.get(id);
  if (!props || props.cohesion == null) return null;
  return typeof props.cohesion === 'number' ? props.cohesion : null;
}

function formatNum(v: number | null): string {
  if (v == null) return '\u2014';
  return v.toFixed(1);
}

export function SimulantTable({
  simulants, selectedSimulantId, chemicalBySimulant, physicalPropsBySimulant, onSelectSimulant,
}: SimulantTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

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
      let va: string | number | null;
      let vb: string | number | null;

      switch (sortKey) {
        case 'name': va = a.name.toLowerCase(); vb = b.name.toLowerCase(); break;
        case 'type': va = (a.type || '').toLowerCase(); vb = (b.type || '').toLowerCase(); break;
        case 'country': va = getCountryDisplay(a.country_code).toLowerCase(); vb = getCountryDisplay(b.country_code).toLowerCase(); break;
        case 'institution': va = (a.institution || '').toLowerCase(); vb = (b.institution || '').toLowerCase(); break;
        case 'availability': va = (a.availability || '').toLowerCase(); vb = (b.availability || '').toLowerCase(); break;
        case 'lunar_sample_reference': va = (a.lunar_sample_reference || '').toLowerCase(); vb = (b.lunar_sample_reference || '').toLowerCase(); break;
        case 'year': va = typeof a.release_date === 'number' ? a.release_date : null; vb = typeof b.release_date === 'number' ? b.release_date : null; break;
        case 'sio2': va = getSiO2(a.simulant_id, chemicalBySimulant); vb = getSiO2(b.simulant_id, chemicalBySimulant); break;
        case 'bulk_density': va = getBulkDensity(a.simulant_id, physicalPropsBySimulant); vb = getBulkDensity(b.simulant_id, physicalPropsBySimulant); break;
        case 'cohesion': va = getCohesion(a.simulant_id, physicalPropsBySimulant); vb = getCohesion(b.simulant_id, physicalPropsBySimulant); break;
        default: return 0;
      }

      // nulls always sort last
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;

      if (typeof va === 'string' && typeof vb === 'string') {
        return va.localeCompare(vb) * dir;
      }
      return ((va as number) - (vb as number)) * dir;
    });

    return arr;
  }, [simulants, sortKey, sortDir, chemicalBySimulant, physicalPropsBySimulant]);

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <span className="w-4" />;
    return sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  const TH = ({ col, label, align = 'left' }: { col: SortKey; label: string; align?: 'left' | 'right' }) => (
    <th
      onClick={() => toggleSort(col)}
      className={cn(
        "py-2.5 px-3 text-xs font-bold text-slate-500 uppercase tracking-wider cursor-pointer select-none hover:text-slate-300 transition-colors whitespace-nowrap sticky top-0 bg-slate-900/95 backdrop-blur-sm z-10",
        align === 'right' && 'text-right',
        sortKey === col && 'text-emerald-400',
      )}
    >
      <span className={cn("inline-flex items-center gap-1", align === 'right' && 'justify-end')}>
        {label}<SortIcon col={col} />
      </span>
    </th>
  );

  return (
    <div className="h-full overflow-auto scrollbar-thin">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-slate-700/50">
            <TH col="name" label="Name" />
            <TH col="type" label="Type" />
            <TH col="country" label="Country" />
            <TH col="institution" label="Institution" />
            <TH col="availability" label="Availability" />
            <TH col="lunar_sample_reference" label="Lunar Ref" />
            <TH col="year" label="Year" align="right" />
            <TH col="sio2" label="SiO2 wt%" align="right" />
            <TH col="bulk_density" label="Bulk Density" align="right" />
            <TH col="cohesion" label="Cohesion" align="right" />
          </tr>
        </thead>
        <tbody>
          {sorted.map((s, i) => {
            const isSelected = s.simulant_id === selectedSimulantId;
            return (
              <tr
                key={s.simulant_id}
                onClick={() => onSelectSimulant(s.simulant_id)}
                className={cn(
                  "cursor-pointer transition-colors border-b border-slate-800/50",
                  isSelected
                    ? "bg-emerald-500/15 hover:bg-emerald-500/20"
                    : i % 2 === 0
                      ? "bg-slate-900/40 hover:bg-slate-800/60"
                      : "bg-slate-900/20 hover:bg-slate-800/60",
                )}
              >
                <td className={cn("py-2 px-3 font-medium whitespace-nowrap", isSelected ? "text-emerald-400" : "text-slate-200")}>{s.name}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.type || '\u2014'}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{getCountryDisplay(s.country_code)}</td>
                <td className="py-2 px-3 text-slate-400 max-w-[200px] truncate">{s.institution || '\u2014'}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.availability || '\u2014'}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.lunar_sample_reference || '\u2014'}</td>
                <td className="py-2 px-3 text-right text-slate-300 font-mono whitespace-nowrap">{typeof s.release_date === 'number' ? s.release_date : '\u2014'}</td>
                <td className="py-2 px-3 text-right text-slate-300 font-mono whitespace-nowrap">{formatNum(getSiO2(s.simulant_id, chemicalBySimulant))}</td>
                <td className="py-2 px-3 text-right text-slate-300 font-mono whitespace-nowrap">{formatNum(getBulkDensity(s.simulant_id, physicalPropsBySimulant))}</td>
                <td className="py-2 px-3 text-right text-slate-300 font-mono whitespace-nowrap">{formatNum(getCohesion(s.simulant_id, physicalPropsBySimulant))}</td>
              </tr>
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
