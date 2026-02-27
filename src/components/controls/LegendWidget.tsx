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
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#10b981] shadow-[0_0_8px_#10b981]" /><span className="text-xs text-slate-300">Mare Simulant</span></div>
              <div className="flex items-center gap-3"><div className="w-3 h-3 rounded-full bg-[#06b6d4] shadow-[0_0_8px_#06b6d4]" /><span className="text-xs text-slate-300">Highlands Simulant</span></div>
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
