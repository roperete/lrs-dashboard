import React from 'react';
import { MapPin, ArrowRightLeft, Rocket } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { Simulant, LunarSite } from '../../types';

function cn(...inputs: any[]) { return twMerge(clsx(inputs)); }

interface SimulantListProps {
  planet: 'earth' | 'moon';
  simulants: Simulant[];
  lunarSites: LunarSite[];
  selectedSimulantId: string | null;
  selectedSimulantId2: string | null;
  selectedLunarSiteId: string | null;
  onSelectSimulant: (id: string) => void;
  onSelectCompare: (id: string) => void;
  onSelectLunarSite: (id: string) => void;
}

export function SimulantList({
  planet, simulants, lunarSites,
  selectedSimulantId, selectedSimulantId2, selectedLunarSiteId,
  onSelectSimulant, onSelectCompare, onSelectLunarSite,
}: SimulantListProps) {
  if (planet === 'earth') {
    if (simulants.length === 0) {
      return <div className="text-center py-8 text-slate-500 italic text-sm">No simulants found.</div>;
    }
    return (
      <div className="space-y-2">
        {simulants.map(sim => (
          <button key={sim.simulant_id}
            onClick={() => onSelectSimulant(sim.simulant_id)}
            className={cn("w-full text-left p-3 rounded-xl transition-all group border",
              selectedSimulantId === sim.simulant_id
                ? "bg-emerald-500/10 border-emerald-500/50"
                : "bg-slate-800/40 border-transparent hover:bg-slate-800/60 hover:border-slate-700")}>
            <div className="flex justify-between items-start mb-1">
              <h3 className={cn("font-semibold transition-colors text-sm",
                selectedSimulantId === sim.simulant_id ? "text-emerald-400" : "text-slate-200 group-hover:text-white")}>
                {sim.name}
              </h3>
              <button onClick={(e) => { e.stopPropagation(); onSelectCompare(sim.simulant_id); }}
                className={cn("p-1.5 rounded-lg transition-all",
                  selectedSimulantId2 === sim.simulant_id ? "bg-blue-500 text-white" : "bg-slate-700 text-slate-400 hover:text-white")}
                title="Compare">
                <ArrowRightLeft size={14} />
              </button>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <MapPin size={12} /><span>{sim.country_code}</span>
              <span className="text-slate-600">|</span>
              <span>{sim.type}</span>
            </div>
          </button>
        ))}
      </div>
    );
  }

  if (lunarSites.length === 0) {
    return <div className="text-center py-8 text-slate-500 italic text-sm">No lunar missions found.</div>;
  }
  return (
    <div className="space-y-2">
      {lunarSites.map(site => (
        <button key={site.id}
          onClick={() => onSelectLunarSite(site.id)}
          className={cn("w-full text-left p-3 rounded-xl transition-all group border",
            selectedLunarSiteId === site.id
              ? "bg-amber-500/10 border-amber-500/50"
              : "bg-slate-800/40 border-transparent hover:bg-slate-800/60 hover:border-slate-700")}>
          <div className="flex justify-between items-start mb-1">
            <h3 className={cn("font-semibold transition-colors",
              selectedLunarSiteId === site.id ? "text-amber-400" : "text-slate-200 group-hover:text-white")}>
              {site.mission}
            </h3>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Rocket size={12} /><span>{site.date}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
