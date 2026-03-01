import React from 'react';

interface LegendWidgetProps {
  planet: 'earth' | 'moon';
  sidebarOpen?: boolean;
}

export function LegendWidget({ planet, sidebarOpen }: LegendWidgetProps) {
  return (
    <div className={`absolute bottom-6 z-[30] pointer-events-none transition-[left] duration-300 ${sidebarOpen ? 'left-[21rem]' : 'left-6'}`}>
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-4 rounded-xl pointer-events-auto">
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">
          {planet === 'earth' ? 'Map Legend' : 'Lunar Missions'}
        </h4>
        <div className="space-y-2">
          {planet === 'earth' ? (
            <>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#d4915c] shadow-[0_0_8px_rgba(212,145,92,0.5)]" /><span className="text-xs text-slate-300">Mare Simulant</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#94a8be] shadow-[0_0_8px_rgba(148,168,190,0.5)]" /><span className="text-xs text-slate-300">Highlands Simulant</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#9b8e82] shadow-[0_0_8px_rgba(155,142,130,0.4)]" /><span className="text-xs text-slate-300">General Simulant</span></div>
            </>
          ) : (
            <>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#f59e0b] shadow-[0_0_8px_#f59e0b]" /><span className="text-xs text-slate-300">Apollo</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#ef4444] shadow-[0_0_8px_#ef4444]" /><span className="text-xs text-slate-300">Luna</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#3b82f6] shadow-[0_0_8px_#3b82f6]" /><span className="text-xs text-slate-300">Chang'e</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#a855f7] shadow-[0_0_8px_#a855f7]" /><span className="text-xs text-slate-300">Other</span></div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
