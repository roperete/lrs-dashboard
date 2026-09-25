import React, { useState, useCallback, useEffect } from 'react';
import { Sun, Moon, Maximize, Minimize, Home, Plus, Minus, Orbit, Navigation } from 'lucide-react';
import { cn } from '../../utils/cn';

interface MapToolbarProps {
  planet: 'earth' | 'moon';
  viewMode: 'globe' | 'map' | 'table';
  earthTexture?: 'day' | 'night';
  onToggleEarthTexture?: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onHome: () => void;
  isRotating?: boolean;
  onToggleRotate?: () => void;
  /** A pane is open on the right: the toolbar moves left of it. */
  paneOpen?: boolean;
  /** "Go to" a place (Earth): the query and its submit. */
  geocodingQuery?: string;
  onGeocodingQueryChange?: (q: string) => void;
  onGeocode?: (e: React.FormEvent) => void;
}

export function MapToolbar({
  planet, viewMode, earthTexture,
  onToggleEarthTexture, onZoomIn, onZoomOut, onHome,
  isRotating, onToggleRotate, paneOpen, geocodingQuery = '', onGeocodingQueryChange, onGeocode,
}: MapToolbarProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [goToOpen, setGoToOpen] = useState(false);

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
    <div className={cn("absolute top-[4.5rem] z-[30] flex flex-col items-end gap-2 md:gap-4 transition-[right] duration-300",
      paneOpen ? "right-2 sm:right-[466px]" : "right-2 md:right-6")}>
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
        {planet === 'earth' && onGeocode && (
          <div className="relative flex items-center">
            {goToOpen && (
              <form onSubmit={(e) => { onGeocode(e); }} className="absolute right-full mr-2 flex bg-slate-900/95 border border-slate-700 rounded-xl p-1 gap-1 shadow-xl">
                <input autoFocus type="text" placeholder="Go to a place…" value={geocodingQuery} aria-label="Go to a place"
                  onChange={(e) => onGeocodingQueryChange?.(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Escape') setGoToOpen(false); }}
                  className="bg-transparent border-none py-1.5 px-2 text-sm focus:outline-none w-48 text-slate-200" />
                <button type="submit" className="px-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 text-xs">Go</button>
              </form>
            )}
            <button onClick={() => setGoToOpen(o => !o)} className={cn(btnClass, goToOpen && 'text-emerald-400 bg-slate-700')}
              title="Go to a place" aria-label="Go to a place" aria-expanded={goToOpen}>
              <Navigation className="w-4 h-4 md:w-5 md:h-5" />
            </button>
          </div>
        )}
        <button onClick={onHome}
          className={btnClass} title="Reset View">
          <Home className="w-4 h-4 md:w-5 md:h-5" />
        </button>
        {viewMode === 'globe' && onToggleRotate && (
          <button onClick={onToggleRotate}
            className={cn(btnClass, isRotating && 'text-emerald-400 bg-slate-700')}
            title={isRotating ? 'Stop Rotation' : 'Auto-Rotate'}>
            <Orbit className="w-4 h-4 md:w-5 md:h-5" />
          </button>
        )}
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
