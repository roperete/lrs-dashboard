import React from 'react';
import { Database, Search, ChevronLeft, ArrowRightLeft } from 'lucide-react';
import { motion } from 'motion/react';
import { FilterPanel } from './FilterPanel';
import { SimulantList } from './SimulantList';
import { ProximitySearch } from './ProximitySearch';
import type { Simulant, LunarSite, FilterState } from '../../types';

interface SidebarProps {
  planet: 'earth' | 'moon';
  searchQuery: string;
  onSearchChange: (q: string) => void;
  filters: FilterState;
  filterOptions: {
    types: string[];
    countries: string[];
    institutions: string[];
    detailedMinerals: string[];
    groupMinerals: string[];
    chemicals: string[];
  };
  setFilter: (key: keyof FilterState, values: string[]) => void;
  clearAllFilters: () => void;
  filteredSimulants: Simulant[];
  lunarSites: LunarSite[];
  selectedSimulantId: string | null;
  selectedSimulantId2: string | null;
  selectedLunarSiteId: string | null;
  onSelectSimulant: (id: string) => void;
  onSelectCompare: (id: string) => void;
  onSelectLunarSite: (id: string) => void;
  onCompareClick: () => void;
  onClose: () => void;
  proximityCenter: [number, number] | null;
  proximityRadius: number;
  onSetProximityCenter: () => void;
  onClearProximityCenter: () => void;
  onProximityRadiusChange: (r: number) => void;
  totalCount: number;
}

export function Sidebar(props: SidebarProps) {
  return (
    <motion.div
      initial={{ x: '-100%' }} animate={{ x: 0 }} exit={{ x: '-100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="absolute left-0 top-0 h-full w-80 max-w-[85vw] bg-slate-900/90 backdrop-blur-xl border-r border-slate-800 z-[50] flex flex-col"
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white tracking-tight">Lunar Regolith Simulants</h2>
            <p className="text-[10px] text-slate-500 uppercase tracking-widest">
              Interactive Database <span className="text-emerald-400 font-semibold">v2.1.0</span>
            </p>
          </div>
          <button onClick={props.onClose} className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-500">
            <ChevronLeft size={18} />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
          <input type="text"
            placeholder={props.planet === 'earth' ? "Search simulants..." : "Search missions..."}
            value={props.searchQuery} onChange={(e) => props.onSearchChange(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition-all" />
        </div>

        {/* Filters (Earth only) */}
        {props.planet === 'earth' && (
          <FilterPanel
            filters={props.filters}
            filterOptions={props.filterOptions}
            setFilter={props.setFilter}
            clearAllFilters={props.clearAllFilters}
          />
        )}

        {/* Proximity Search (Earth only) */}
        {props.planet === 'earth' && (
          <ProximitySearch
            proximityCenter={props.proximityCenter}
            proximityRadius={props.proximityRadius}
            onSetCenter={props.onSetProximityCenter}
            onClearCenter={props.onClearProximityCenter}
            onRadiusChange={props.onProximityRadiusChange}
          />
        )}

        {/* Compare button */}
        {props.planet === 'earth' && props.selectedSimulantId && props.selectedSimulantId2 && (
          <button onClick={props.onCompareClick}
            className="w-full py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/20">
            <ArrowRightLeft size={14} />Compare Selected
          </button>
        )}
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 pt-2 custom-scrollbar">
        <SimulantList
          planet={props.planet}
          simulants={props.filteredSimulants}
          lunarSites={props.lunarSites}
          selectedSimulantId={props.selectedSimulantId}
          selectedSimulantId2={props.selectedSimulantId2}
          selectedLunarSiteId={props.selectedLunarSiteId}
          onSelectSimulant={props.onSelectSimulant}
          onSelectCompare={props.onSelectCompare}
          onSelectLunarSite={props.onSelectLunarSite}
        />
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-slate-800 space-y-3">
        <div className="text-center">
          <span className="text-xs text-slate-500">
            {props.planet === 'earth'
              ? `${props.filteredSimulants.length} / ${props.totalCount} simulants`
              : `${props.lunarSites.length} missions`}
          </span>
        </div>

        {/* CNES Sponsor Badge */}
        <a href="https://cnes.fr" target="_blank" rel="noopener noreferrer"
          className="flex flex-col items-center gap-1.5 p-2.5 bg-white/[0.03] border border-white/[0.08] rounded-lg no-underline transition-colors hover:bg-white/[0.08]">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">Sponsored by</span>
          <img src={import.meta.env.BASE_URL + 'assets/cnes-logo.png'} alt="CNES" className="h-10 w-auto object-contain" />
        </a>
      </div>
    </motion.div>
  );
}
