import React, { useState, useCallback, useEffect } from 'react';
import { Layers, Locate, MousePointer2, Square, ChevronRight, Maximize, Minimize } from 'lucide-react';
import { cn } from '../../utils/cn';

interface MapToolbarProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map' | 'table';
  drawingMode: 'none' | 'marker' | 'polygon';
  tempPolygonPointsCount: number;
  onToggleEarthTexture?: () => void;
  onLocate: () => void;
  onSetDrawingMode: (mode: 'none' | 'marker' | 'polygon') => void;
  onFinishPolygon: () => void;
}

export function MapToolbar({
  planet, viewMode, drawingMode, tempPolygonPointsCount,
  onToggleEarthTexture, onLocate, onSetDrawingMode, onFinishPolygon,
}: MapToolbarProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }, []);

  return (
    <div className="absolute right-4 md:right-6 top-24 z-[30] flex flex-col gap-4">
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-2 rounded-2xl flex flex-col gap-2">
        <button onClick={toggleFullscreen}
          className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 hover:text-emerald-400 transition-all shadow-lg" title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
          {isFullscreen ? <Minimize size={20} /> : <Maximize size={20} />}
        </button>
        {planet === 'earth' && viewMode === 'globe' && onToggleEarthTexture && (
          <button onClick={onToggleEarthTexture}
            className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 hover:text-emerald-400 transition-all shadow-lg" title="Toggle Day/Night">
            <Layers size={20} />
          </button>
        )}
        {planet === 'earth' && (
          <button onClick={onLocate}
            className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 hover:text-emerald-400 transition-all shadow-lg" title="My Location">
            <Locate size={20} />
          </button>
        )}
      </div>

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
