import React, { useState } from 'react';
import { ChevronDown, ChevronRight, MapPin } from 'lucide-react';
import type { Composition, MineralSourcing } from '../../types';

interface MineralSourcingSectionProps {
  compositions: Composition[];
  mineralSourcingByMineral: Map<string, MineralSourcing>;
}

export function MineralSourcingSection({ compositions, mineralSourcingByMineral }: MineralSourcingSectionProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  // Match composition minerals to sourcing data
  const mineralsWithSourcing = compositions
    .map(c => ({
      composition: c,
      sourcing: mineralSourcingByMineral.get(c.component_name?.toLowerCase()) ||
                mineralSourcingByMineral.get(c.mineral_name?.toLowerCase()),
    }))
    .filter(m => m.sourcing);

  if (mineralsWithSourcing.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Mineral Sourcing</h3>
      <div className="space-y-1.5">
        {mineralsWithSourcing.map(({ composition, sourcing }) => {
          const name = composition.component_name || composition.mineral_name;
          const isOpen = expanded === name;

          return (
            <div key={name} className="bg-slate-800/50 rounded-lg border border-slate-700/50 overflow-hidden">
              <button
                onClick={() => setExpanded(isOpen ? null : name)}
                className="w-full flex items-center justify-between p-2.5 hover:bg-slate-700/30 transition-colors text-left"
              >
                <div className="flex items-center gap-2">
                  {isOpen ? <ChevronDown size={14} className="text-slate-500" /> : <ChevronRight size={14} className="text-slate-500" />}
                  <span className="text-sm font-medium text-slate-200">{name}</span>
                  <span className="text-xs text-slate-500">
                    {composition.value_pct || composition.percentage}%
                  </span>
                </div>
                {sourcing!.available_europe && (
                  <span className="text-[10px] px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded-full">EU</span>
                )}
              </button>

              {isOpen && sourcing && (
                <div className="px-3 pb-3 pt-1 space-y-2 border-t border-slate-700/30">
                  {sourcing.source_mineral && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Source Mineral</p>
                      <p className="text-xs text-slate-300">{sourcing.source_mineral}</p>
                    </div>
                  )}
                  {sourcing.chemistry && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Chemistry</p>
                      <p className="text-xs text-slate-300">{sourcing.chemistry}</p>
                    </div>
                  )}
                  {sourcing.description_simple && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Description</p>
                      <p className="text-xs text-slate-300">{sourcing.description_simple}</p>
                    </div>
                  )}
                  {(sourcing.mining_locations || sourcing.mineral_locations) && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                        <MapPin size={10} /> Mining Locations
                      </p>
                      <p className="text-xs text-slate-300">{sourcing.mining_locations || sourcing.mineral_locations}</p>
                    </div>
                  )}
                  {sourcing.supplier && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Supplier</p>
                      <p className="text-xs text-emerald-400">{sourcing.supplier}</p>
                    </div>
                  )}
                  {sourcing.ethical_compliance && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Compliance</p>
                      <p className="text-xs text-slate-300">{sourcing.ethical_compliance}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
