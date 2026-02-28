import React, { useState } from 'react';
import { Database, Search, ChevronLeft, ArrowRightLeft, ChevronDown, MessageSquare, HelpCircle, X } from 'lucide-react';
import { motion } from 'motion/react';
import { DynamicFilterPanel } from './DynamicFilterPanel';
import { SimulantList } from './SimulantList';
import type { Simulant, LunarSite, DynamicFilter, FilterProperty } from '../../types';

interface SidebarProps {
  planet: 'earth' | 'moon';
  searchQuery: string;
  onSearchChange: (q: string) => void;
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
  totalCount: number;
}

export function Sidebar(props: SidebarProps) {
  const [listOpen, setListOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);

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
              Interactive Database <span className="text-emerald-400 font-semibold">v2.8.2</span>
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

        {/* Dynamic Filters (Earth only) */}
        {props.planet === 'earth' && (
          <DynamicFilterPanel
            filters={props.filters}
            filterOptions={props.filterOptions}
            onAddFilter={props.onAddFilter}
            onUpdateFilter={props.onUpdateFilter}
            onRemoveFilter={props.onRemoveFilter}
            onClearAll={props.clearAllFilters}
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

      {/* Collapsible simulant list */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 pt-2 custom-scrollbar">
        <button
          onClick={() => setListOpen(!listOpen)}
          className="w-full flex items-center justify-between py-2 px-1 text-xs font-bold uppercase tracking-wider text-slate-500 hover:text-slate-300 transition-colors"
        >
          <span>
            {props.planet === 'earth'
              ? `All Simulants (${props.filteredSimulants.length})`
              : `All Missions (${props.lunarSites.length})`}
          </span>
          <ChevronDown size={14} className={`transition-transform ${listOpen ? 'rotate-180' : ''}`} />
        </button>
        {listOpen && (
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
        )}
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

        <div className="flex gap-2">
          <a
            href="https://thespringinstitute.com/contact-us/"
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-2 py-2 bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/50 rounded-lg text-xs text-slate-500 hover:text-slate-300 transition-all no-underline"
          >
            <MessageSquare size={12} />Feedback
          </a>
          <button
            onClick={() => setHelpOpen(true)}
            className="flex items-center justify-center gap-2 py-2 px-3 bg-slate-800/40 hover:bg-slate-800/70 border border-slate-700/50 rounded-lg text-xs text-slate-500 hover:text-slate-300 transition-all"
          >
            <HelpCircle size={12} />Help
          </button>
        </div>

        {/* CNES Sponsor Badge */}
        <a href="https://cnes.fr" target="_blank" rel="noopener noreferrer"
          className="flex flex-col items-center gap-1.5 p-2.5 bg-white/[0.03] border border-white/[0.08] rounded-lg no-underline transition-colors hover:bg-white/[0.08]">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider">Sponsored by</span>
          <img src={import.meta.env.BASE_URL + 'assets/cnes-logo.png'} alt="CNES" className="h-10 w-auto object-contain" />
        </a>
      </div>

      {/* Help modal */}
      {helpOpen && (
        <div className="absolute inset-0 z-[60] bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setHelpOpen(false)}>
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-h-[80vh] overflow-y-auto w-full shadow-2xl"
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-slate-800 sticky top-0 bg-slate-900 rounded-t-2xl">
              <h3 className="text-sm font-bold text-white">Quick Guide</h3>
              <button onClick={() => setHelpOpen(false)} className="p-1 hover:bg-slate-800 rounded-lg text-slate-500">
                <X size={16} />
              </button>
            </div>
            <div className="p-4 space-y-4 text-xs text-slate-300 leading-relaxed">
              <div>
                <h4 className="text-emerald-400 font-bold mb-1">Views</h4>
                <p>Switch between <b>3D Globe</b>, <b>2D Map</b>, and <b>Table</b> using the header buttons. Toggle <b>Earth</b> (simulants) or <b>Moon</b> (landing sites).</p>
              </div>
              <div>
                <h4 className="text-emerald-400 font-bold mb-1">Search & Filter</h4>
                <p>Type to search by name. Click <b>"Add Filter"</b> to filter by type, country, institution, availability, minerals, oxides, year, and more. Filters combine with AND logic.</p>
              </div>
              <div>
                <h4 className="text-emerald-400 font-bold mb-1">Simulant Details</h4>
                <p>Click any marker or list item to open the detail panel with properties, mineral/chemical composition charts, and references.</p>
              </div>
              <div>
                <h4 className="text-emerald-400 font-bold mb-1">Lunar Reference</h4>
                <p>In the detail panel, select a lunar reference (Apollo, Luna, Chang'e) from the dropdown to overlay real Moon sample data onto the charts. Click <b>"Full comparison view"</b> for a dedicated comparison with delta values.</p>
              </div>
              <div>
                <h4 className="text-emerald-400 font-bold mb-1">Compare Simulants</h4>
                <p>Check 2 simulants in the table and click <b>"Compare"</b>, or use the compare button in the detail panel. View side-by-side charts or a delta table.</p>
              </div>
              <div>
                <h4 className="text-emerald-400 font-bold mb-1">Export</h4>
                <p>Use the export button (bottom-right) to download CSV files — single simulant, filtered set, or the full database.</p>
              </div>
              <div>
                <h4 className="text-emerald-400 font-bold mb-1">Map Controls</h4>
                <p>Right toolbar: fullscreen, day/night toggle (3D Earth), GPS location, home (reset view), and <b>+/−</b> zoom buttons. You can also scroll to zoom and drag to pan.</p>
              </div>
              <div className="pt-2 border-t border-slate-800">
                <p className="text-slate-500">An initiative by <b className="text-slate-400">The Spring Institute for Forests on the Moon</b>, sponsored by <b className="text-slate-400">CNES Spaceship</b>.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
