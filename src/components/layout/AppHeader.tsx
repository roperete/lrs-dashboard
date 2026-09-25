import React from 'react';
import {
  Database, Earth as EarthIcon, Moon as MoonIcon, Globe as GlobeIcon,
  Map as MapIcon, Table2, PanelLeft, HelpCircle, MessageSquare,
} from 'lucide-react';
import { cn } from '../../utils/cn';

/** Height of the top bar; the side panes start below it (see TOP_BAR_OFFSET users). */
export const TOP_BAR_HEIGHT = 'h-14';

interface AppHeaderProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map' | 'table';
  sidebarOpen: boolean;
  /** Active filters and search, shown on the pane toggle when the pane is closed. */
  filterCount: number;
  onToggleSidebar: () => void;
  onPlanetChange: (p: 'earth' | 'moon') => void;
  onViewModeChange: (v: 'globe' | 'map' | 'table') => void;
  onOpenHelp: () => void;
  /** The Export menu, rendered in the bar. */
  exportSlot?: React.ReactNode;
}

/**
 * The fixed top bar. Everything that changes what the page shows lives here, above the side
 * panes, so an open pane can never cover the view switch or Export (review #3).
 */
export function AppHeader({
  planet, viewMode, sidebarOpen, filterCount,
  onToggleSidebar, onPlanetChange, onViewModeChange, onOpenHelp, exportSlot,
}: AppHeaderProps) {
  const seg = (active: boolean, activeClass: string) => cn(
    'flex items-center gap-1.5 px-3 h-9 rounded-lg text-sm font-medium transition-colors',
    active ? activeClass : 'text-slate-300 hover:text-white hover:bg-slate-800',
  );
  return (
    <header className={cn('fixed top-0 inset-x-0 z-[1200] flex items-center gap-2 md:gap-3 px-2 md:px-4 bg-slate-950/95 backdrop-blur-md border-b border-slate-800', TOP_BAR_HEIGHT)}>
      <button onClick={onToggleSidebar} aria-label={sidebarOpen ? 'Close the Find pane' : 'Open the Find pane'} aria-pressed={sidebarOpen}
        className={cn('relative flex items-center justify-center w-10 h-10 rounded-lg transition-colors',
          sidebarOpen ? 'bg-slate-800 text-emerald-400' : 'text-slate-300 hover:text-white hover:bg-slate-800')}>
        <PanelLeft size={20} />
        {!sidebarOpen && filterCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold bg-emerald-500 text-slate-950 rounded-full">
            {filterCount}
          </span>
        )}
      </button>

      <div className="flex items-center gap-2 min-w-0">
        <div className="p-1.5 bg-emerald-500 rounded-lg shrink-0"><Database size={18} className="text-slate-950" /></div>
        <h1 className="text-base font-bold tracking-tight text-white truncate">
          <span className="hidden lg:inline">Lunar Regolith Simulant <span className="text-emerald-400">Database</span></span>
          <span className="lg:hidden">LRS <span className="text-emerald-400">Database</span></span>
        </h1>
      </div>

      <div className="ml-auto flex items-center gap-1.5 md:gap-3">
        <div role="group" aria-label="Planet" className="bg-slate-900 border border-slate-800 p-0.5 rounded-xl flex gap-0.5">
          <button onClick={() => onPlanetChange('earth')} aria-pressed={planet === 'earth'} className={seg(planet === 'earth', 'bg-emerald-500 text-slate-950')}>
            <EarthIcon size={16} /><span className="hidden sm:inline">Earth</span>
          </button>
          <button onClick={() => onPlanetChange('moon')} aria-pressed={planet === 'moon'} className={seg(planet === 'moon', 'bg-amber-500 text-slate-950')}>
            <MoonIcon size={16} /><span className="hidden sm:inline">Moon</span>
          </button>
        </div>

        <div role="group" aria-label="View" className="bg-slate-900 border border-slate-800 p-0.5 rounded-xl flex gap-0.5">
          <button onClick={() => onViewModeChange('globe')} aria-pressed={viewMode === 'globe'} className={seg(viewMode === 'globe', 'bg-slate-200 text-slate-950')}>
            <GlobeIcon size={16} /><span className="hidden sm:inline">Globe</span>
          </button>
          <button onClick={() => onViewModeChange('map')} aria-pressed={viewMode === 'map'} className={seg(viewMode === 'map', 'bg-slate-200 text-slate-950')}>
            <MapIcon size={16} /><span className="hidden sm:inline">Map</span>
          </button>
          <button onClick={() => onViewModeChange('table')} aria-pressed={viewMode === 'table'} className={seg(viewMode === 'table', 'bg-slate-200 text-slate-950')}>
            <Table2 size={16} /><span className="hidden sm:inline">Table</span>
          </button>
        </div>

        {exportSlot}

        <a href="https://thespringinstitute.com/contact-us/" target="_blank" rel="noopener noreferrer" aria-label="Feedback"
          className="hidden md:flex items-center justify-center w-10 h-10 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800" title="Feedback">
          <MessageSquare size={18} />
        </a>
        <button onClick={onOpenHelp} aria-label="Help" title="Help"
          className="flex items-center justify-center w-10 h-10 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800">
          <HelpCircle size={18} />
        </button>
      </div>
    </header>
  );
}
