import React from 'react';
import { Target, X, Locate } from 'lucide-react';

interface ProximitySearchProps {
  proximityCenter: [number, number] | null;
  proximityRadius: number;
  onSetCenter: () => void;
  onClearCenter: () => void;
  onRadiusChange: (radius: number) => void;
}

export function ProximitySearch({
  proximityCenter, proximityRadius,
  onSetCenter, onClearCenter, onRadiusChange,
}: ProximitySearchProps) {
  return (
    <div className="bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Target size={14} className="text-emerald-400" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Proximity Search</span>
        </div>
        {proximityCenter && (
          <button onClick={onClearCenter} className="text-slate-500 hover:text-white"><X size={14} /></button>
        )}
      </div>
      {!proximityCenter ? (
        <button onClick={onSetCenter}
          className="w-full py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-2">
          <Locate size={14} />Set Center Point
        </button>
      ) : (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[10px] text-slate-500">
            <span>Radius: {proximityRadius} km</span>
          </div>
          <input type="range" min="100" max="10000" step="100" value={proximityRadius}
            onChange={(e) => onRadiusChange(parseInt(e.target.value))} className="w-full accent-emerald-500" />
        </div>
      )}
    </div>
  );
}
