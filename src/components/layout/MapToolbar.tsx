import React, { useState, useCallback, useEffect } from 'react';
import { Sun, Moon, Maximize, Minimize, Home, Plus, Minus } from 'lucide-react';
import { cn } from '../../utils/cn';

interface MapToolbarProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map' | 'table';
  earthTexture?: 'day' | 'night';
  onToggleEarthTexture?: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onHome: () => void;
}

export function MapToolbar({
  planet, viewMode, earthTexture,
  onToggleEarthTexture, onZoomIn, onZoomOut, onHome,
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

  const btnClass = "p-2 md:p-3 bg-slate-800 hover:bg-slate-700 rounded-lg md:rounded-xl text-slate-400 hover:text-emerald-400 transition-all shadow-lg";
  const iconSize = 16;
  const iconSizeMd = 20;

  return (
    <div className="absolute right-2 md:right-6 top-16 md:top-24 z-[30] flex flex-col gap-2 md:gap-4">
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-1.5 md:p-2 rounded-xl md:rounded-2xl flex flex-col gap-1.5 md:gap-2">
        <button onClick={toggleFullscreen}
          className={btnClass} title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}>
          {isFullscreen ? <Minimize className="w-4 h-4 md:w-5 md:h-5" /> : <Maximize className="w-4 h-4 md:w-5 md:h-5" />}
        </button>
        {planet === 'earth' && viewMode === 'globe' && onToggleEarthTexture && (
          <button onClick={onToggleEarthTexture}
            className={btnClass} title={earthTexture === 'night' ? 'Switch to Day' : 'Switch to Night'}>
            {earthTexture === 'night' ? <Sun className="w-4 h-4 md:w-5 md:h-5" /> : <Moon className="w-4 h-4 md:w-5 md:h-5" />}
          </button>
        )}
        <button onClick={onHome}
          className={btnClass} title="Reset View">
          <Home className="w-4 h-4 md:w-5 md:h-5" />
        </button>
      </div>
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-1.5 md:p-2 rounded-xl md:rounded-2xl flex flex-col gap-1.5 md:gap-2">
        <button onClick={onZoomIn} className={btnClass} title="Zoom In">
          <Plus className="w-4 h-4 md:w-5 md:h-5" />
        </button>
        <button onClick={onZoomOut} className={btnClass} title="Zoom Out">
          <Minus className="w-4 h-4 md:w-5 md:h-5" />
        </button>
      </div>
    </div>
  );
}
