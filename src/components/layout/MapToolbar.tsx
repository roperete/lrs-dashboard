import React from 'react';
import { Layers, Locate, MousePointer2, Square, ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';

interface MapToolbarProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map';
  drawingMode: 'none' | 'marker' | 'polygon';
  tempPolygonPointsCount: number;
  onToggleBaseLayer: () => void;
  onLocate: () => void;
  onSetDrawingMode: (mode: 'none' | 'marker' | 'polygon') => void;
  onFinishPolygon: () => void;
}

export function MapToolbar({
  planet, viewMode, drawingMode, tempPolygonPointsCount,
  onToggleBaseLayer, onLocate, onSetDrawingMode, onFinishPolygon,
}: MapToolbarProps) {
  return (
    <div className="absolute right-6 top-24 z-[30] flex flex-col gap-4">
      {planet === 'earth' && (
        <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-2 rounded-2xl flex flex-col gap-2">
          <button onClick={onToggleBaseLayer}
            className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 hover:text-emerald-400 transition-all shadow-lg" title="Toggle Base Layer">
            <Layers size={20} />
          </button>
          <button onClick={onLocate}
            className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 hover:text-emerald-400 transition-all shadow-lg" title="My Location">
            <Locate size={20} />
          </button>
        </div>
      )}

      {viewMode === 'map' && planet === 'earth' && (
        <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-2 rounded-2xl flex flex-col gap-2">
          <button onClick={() => onSetDrawingMode(drawingMode === 'marker' ? 'none' : 'marker')}
            className={cn("p-3 rounded-xl transition-all shadow-lg",
              drawingMode === 'marker' ? "bg-emerald-500 text-slate-950" : "bg-slate-800 text-slate-400 hover:text-emerald-400")}
            title="Add Custom Marker">
            <MousePointer2 size={20} />
          </button>
          <button onClick={() => onSetDrawingMode(drawingMode === 'polygon' ? 'none' : 'polygon')}
            className={cn("p-3 rounded-xl transition-all shadow-lg",
              drawingMode === 'polygon' ? "bg-emerald-500 text-slate-950" : "bg-slate-800 text-slate-400 hover:text-emerald-400")}
            title="Draw Polygon">
            <Square size={20} />
          </button>
          {drawingMode === 'polygon' && tempPolygonPointsCount >= 3 && (
            <button onClick={onFinishPolygon}
              className="p-3 bg-emerald-500 text-slate-950 rounded-xl transition-all shadow-lg animate-pulse" title="Finish Polygon">
              <ChevronRight size={20} />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
