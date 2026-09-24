import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';
import { cn } from '../../utils/cn';
import { Tooltip } from '../ui/Tooltip';
import type { LunarSite } from '../../types';

type SortDir = 'asc' | 'desc';
type SortKey = 'name' | 'mission' | 'date' | 'type' | 'samples';

/** One-line explanation of each column, shown on hover over the header. */
const COLUMN_HELP: Record<SortKey | 'density' | 'friction' | 'cohesion', string> = {
  name: 'Landing site, named after the mission and the region it landed in.',
  mission: 'The mission that landed there.',
  type: 'Programme: Apollo (US, crewed), Luna (Soviet, robotic), Chang\'e (China, robotic), or another lander.',
  date: 'Landing date.',
  samples: 'Mass of lunar material brought back to Earth. Only crewed and sample-return missions return any.',
  density: 'Bulk density of the regolith at the site, in g/cm³: mass per volume including the pore space, from in-situ measurements or returned cores.',
  friction: 'Internal angle of friction of the regolith, in degrees, from in-situ soil-mechanics measurements. Governs slope stability and bearing capacity.',
  cohesion: 'Shear strength of the regolith at zero normal stress, in kPa: how much the grains hold together.',
};

interface LunarSampleTableProps {
  sites: LunarSite[];
  selectedSiteId: string | null;
  onSelectSite: (id: string) => void;
}

export function LunarSampleTable({ sites, selectedSiteId, onSelectSite }: LunarSampleTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const sorted = useMemo(() => {
    const arr = [...sites];
    const dir = sortDir === 'asc' ? 1 : -1;
    arr.sort((a, b) => {
      let va: string, vb: string;
      switch (sortKey) {
        case 'name': va = a.name.toLowerCase(); vb = b.name.toLowerCase(); break;
        case 'mission': va = a.mission.toLowerCase(); vb = b.mission.toLowerCase(); break;
        case 'date': va = a.date; vb = b.date; break;
        case 'type': va = a.type.toLowerCase(); vb = b.type.toLowerCase(); break;
        case 'samples': va = (a.samples_returned || '').toLowerCase(); vb = (b.samples_returned || '').toLowerCase(); break;
        default: return 0;
      }
      return va.localeCompare(vb) * dir;
    });
    return arr;
  }, [sites, sortKey, sortDir]);

  const SortIcon = ({ col }: { col: SortKey }) => {
    if (sortKey !== col) return <span className="w-4" />;
    return sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />;
  };

  const TH = ({ col, label }: { col: SortKey; label: string }) => (
    <th
      onClick={() => toggleSort(col)}
      className={cn(
        "py-2.5 px-3 text-xs font-bold text-slate-500 uppercase tracking-wider cursor-pointer select-none hover:text-slate-300 transition-colors whitespace-nowrap sticky top-0 bg-slate-900/95 backdrop-blur-sm z-10",
        sortKey === col && 'text-amber-400',
      )}
    >
      <Tooltip text={COLUMN_HELP[col]} align="left">
        <span className="inline-flex items-center gap-1">{label}<SortIcon col={col} /></span>
      </Tooltip>
    </th>
  );

  /** A header the table does not sort by, with its explanation on hover. */
  const Plain = ({ help, label }: { help: string; label: string }) => (
    <th className="py-2.5 px-3 text-xs font-bold text-slate-500 uppercase tracking-wider whitespace-nowrap sticky top-0 bg-slate-900/95 backdrop-blur-sm z-10 text-right">
      <Tooltip text={help} align="right"><span>{label}</span></Tooltip>
    </th>
  );

  const missionColor: Record<string, string> = {
    Apollo: 'text-amber-400',
    Luna: 'text-red-400',
    'Chang-e': 'text-blue-400',
  };

  return (
    <div className="h-full overflow-auto scrollbar-thin">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-slate-700/50">
            <TH col="name" label="Site" />
            <TH col="mission" label="Mission" />
            <TH col="type" label="Program" />
            <TH col="date" label="Date" />
            <TH col="samples" label="Samples" />
            <Plain label="Density" help={COLUMN_HELP.density} />
            <Plain label="Friction" help={COLUMN_HELP.friction} />
            <Plain label="Cohesion" help={COLUMN_HELP.cohesion} />
          </tr>
        </thead>
        <tbody>
          {sorted.map((s, i) => {
            const isSelected = s.id === selectedSiteId;
            return (
              <tr
                key={s.id}
                onClick={() => onSelectSite(s.id)}
                className={cn(
                  "cursor-pointer transition-colors border-b border-slate-800/50",
                  isSelected
                    ? "bg-amber-500/15 hover:bg-amber-500/20"
                    : i % 2 === 0
                      ? "bg-slate-900/40 hover:bg-slate-800/60"
                      : "bg-slate-900/20 hover:bg-slate-800/60",
                )}
              >
                <td className={cn("py-2 px-3 font-medium", isSelected ? "text-amber-400" : "text-slate-200")}>{s.name}</td>
                <td className={cn("py-2 px-3 font-medium whitespace-nowrap", missionColor[s.type] || 'text-purple-400')}>{s.mission}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.type}</td>
                <td className="py-2 px-3 text-slate-400 whitespace-nowrap">{s.date}</td>
                <td className="py-2 px-3 text-slate-300 whitespace-nowrap">{s.samples_returned || '\u2014'}</td>
                <td className="py-2 px-3 text-slate-400 text-right font-mono whitespace-nowrap">{s.geotechnical?.bulk_density ?? '\u2014'}</td>
                <td className="py-2 px-3 text-slate-400 text-right font-mono whitespace-nowrap">{s.geotechnical?.friction_angle != null ? `${s.geotechnical.friction_angle}\u00B0` : '\u2014'}</td>
                <td className="py-2 px-3 text-slate-400 text-right font-mono whitespace-nowrap">{s.geotechnical?.cohesion != null ? `${s.geotechnical.cohesion} kPa` : '\u2014'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {sorted.length === 0 && (
        <div className="flex items-center justify-center h-40 text-slate-500 text-sm">
          No lunar sites found.
        </div>
      )}
    </div>
  );
}
