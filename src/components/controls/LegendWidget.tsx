import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '../../utils/cn';

interface LegendWidgetProps {
  planet: 'earth' | 'moon';
  sidebarOpen?: boolean;
}

export function LegendWidget({ planet, sidebarOpen }: LegendWidgetProps) {
  // Open where there is room for it; on phones it starts as a button (owner, 2026-10-26)
  const [open, setOpen] = useState(() => window.innerWidth >= 640);
  const title = planet === 'earth' ? 'Map Legend' : 'Lunar Missions';
  return (
    // on phones the open Find pane covers the map, so the legend goes with it
    <div className={cn('absolute bottom-6 z-[30] pointer-events-none transition-[left] duration-300',
      sidebarOpen ? 'left-[21rem] max-sm:hidden' : 'left-4 sm:left-6')}>
      <div className={cn('bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-xl pointer-events-auto', open ? 'p-4' : 'p-0')}>
        <button type="button" onClick={() => setOpen(o => !o)} aria-expanded={open}
          className={cn('flex w-full items-center justify-between gap-3 text-xs font-semibold text-slate-300 hover:text-white', open ? 'mb-3' : 'px-3 py-2')}>
          {title}
          {open ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
        {open && <div className="space-y-2">
          {planet === 'earth' ? (
            <>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#d4915c] shadow-[0_0_8px_rgba(212,145,92,0.5)]" /><span className="text-xs text-slate-300">Mare Simulant</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#94a8be] shadow-[0_0_8px_rgba(148,168,190,0.5)]" /><span className="text-xs text-slate-300">Highlands Simulant</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#9b8e82] shadow-[0_0_8px_rgba(155,142,130,0.4)]" /><span className="text-xs text-slate-300">General, and other types</span></div>
              <p className="text-[11px] text-slate-400 max-w-[190px] pt-1">Dust, icy, mechanical and speciality simulants use the General colour. A pin is where the producer is, or where its rock comes from.</p>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#f59e0b] shadow-[0_0_8px_#f59e0b]" /><span className="text-xs text-slate-300">Apollo</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#ef4444] shadow-[0_0_8px_#ef4444]" /><span className="text-xs text-slate-300">Luna</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#3b82f6] shadow-[0_0_8px_#3b82f6]" /><span className="text-xs text-slate-300">Chang'e</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#a855f7] shadow-[0_0_8px_#a855f7]" /><span className="text-xs text-slate-300">Other</span></div>
            </>
          )}
        </div>}
      </div>
    </div>
  );
}
