import React, { useState, useCallback, useEffect } from 'react';
import { Layers, Locate, Maximize, Minimize, Home } from 'lucide-react';
import { cn } from '../../utils/cn';

interface MapToolbarProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map' | 'table';
  onToggleEarthTexture?: () => void;
  onLocate: () => void;
  onHome: () => void;
}

export function MapToolbar({
  planet, viewMode,
  onToggleEarthTexture, onLocate, onHome,
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
        <button onClick={onHome}
          className="p-3 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-400 hover:text-emerald-400 transition-all shadow-lg" title="Reset View">
          <Home size={20} />
        </button>
      </div>
    </div>
  );
}
