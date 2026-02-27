import React from 'react';
import {
  Database, Globe as GlobeIcon, Moon as MoonIcon,
  Map as MapIcon, Table2, Navigation, ChevronRight,
} from 'lucide-react';
import { cn } from '../../utils/cn';

interface AppHeaderProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map' | 'table';
  geocodingQuery: string;
  sidebarOpen?: boolean;
  onPlanetChange: (p: 'earth' | 'moon') => void;
  onViewModeChange: (v: 'globe' | 'map' | 'table') => void;
  onGeocodingQueryChange: (q: string) => void;
  onGeocode: (e: React.FormEvent) => void;
}

export function AppHeader({
  planet, viewMode, geocodingQuery, sidebarOpen,
  onPlanetChange, onViewModeChange, onGeocodingQueryChange, onGeocode,
}: AppHeaderProps) {
  return (
    <header className="absolute top-0 left-0 w-full p-4 md:p-6 z-[40] pointer-events-none">
      <div className="flex flex-wrap justify-between items-start gap-3">
        {/* Title — hidden on mobile to save space, shifts right when sidebar open */}
        <div className={`pointer-events-auto hidden md:block transition-[margin] duration-300 ${sidebarOpen ? 'ml-[21rem]' : ''}`}>
          <div className="flex items-center gap-3 mb-1">
            <div className="p-2 bg-emerald-500 rounded-lg shadow-[0_0_20px_rgba(16,185,129,0.4)]">
              <Database size={24} className="text-slate-950" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">Lunar Regolith Simulant <span className="text-emerald-500">Database</span></h1>
          </div>
          <p className="text-xs text-slate-400 font-mono uppercase tracking-[0.2em] ml-12">
            Interactive Research Tool
          </p>
        </div>

        <div className="flex items-center gap-2 md:gap-4 pointer-events-auto ml-auto">
          {/* Planet toggle */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-1 rounded-xl flex gap-1">
            <button onClick={() => onPlanetChange('earth')}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-sm font-medium transition-all",
                planet === 'earth' ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white")}>
              <GlobeIcon size={16} /><span className="hidden sm:inline">Earth</span>
            </button>
            <button onClick={() => onPlanetChange('moon')}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-sm font-medium transition-all",
                planet === 'moon' ? "bg-amber-500 text-slate-950" : "text-slate-400 hover:text-white")}>
              <MoonIcon size={16} /><span className="hidden sm:inline">Moon</span>
            </button>
          </div>

          {/* View mode toggle */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-1 rounded-xl flex gap-1">
            <button onClick={() => onViewModeChange('globe')}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-sm font-medium transition-all",
                viewMode === 'globe' ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white")}>
              <GlobeIcon size={16} /><span className="hidden sm:inline">3D</span>
            </button>
            <button onClick={() => onViewModeChange('map')}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-sm font-medium transition-all",
                viewMode === 'map' ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white")}>
              <MapIcon size={16} /><span className="hidden sm:inline">2D</span>
            </button>
            <button onClick={() => onViewModeChange('table')}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 md:px-4 md:py-2 rounded-lg text-sm font-medium transition-all",
                viewMode === 'table' ? "bg-emerald-500 text-slate-950" : "text-slate-400 hover:text-white")}>
              <Table2 size={16} /><span className="hidden sm:inline">Table</span>
            </button>
          </div>

          {/* Geocoding (Earth only, hidden on mobile) */}
          {planet === 'earth' && (
            <form onSubmit={onGeocode} className="hidden lg:flex bg-slate-900/80 backdrop-blur-md border border-slate-800 p-1 rounded-xl gap-1">
              <div className="relative">
                <Navigation className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={14} />
                <input type="text" placeholder="Go to address..." value={geocodingQuery}
                  onChange={(e) => onGeocodingQueryChange(e.target.value)}
                  className="bg-transparent border-none py-2 pl-9 pr-4 text-sm focus:outline-none w-48" />
              </div>
              <button type="submit" className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-400 transition-colors">
                <ChevronRight size={18} />
              </button>
            </form>
          )}
        </div>
      </div>
    </header>
  );
}
