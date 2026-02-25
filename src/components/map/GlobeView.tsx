import React, { useRef, forwardRef, useImperativeHandle } from 'react';
import Globe, { GlobeMethods } from 'react-globe.gl';

export interface GlobeViewHandle {
  pointOfView: (coords: { lat: number; lng: number; altitude: number }, ms: number) => void;
}

interface GlobeViewProps {
  planet: 'earth' | 'moon';
  baseLayer: 'satellite' | 'streets';
  globeData: any[];
  onPointClick: (point: any) => void;
}

export const GlobeView = forwardRef<GlobeViewHandle, GlobeViewProps>(
  ({ planet, baseLayer, globeData, onPointClick }, ref) => {
    const globeRef = useRef<GlobeMethods>(null);

    useImperativeHandle(ref, () => ({
      pointOfView: (coords, ms) => globeRef.current?.pointOfView(coords, ms),
    }));

    return (
      <Globe
        ref={globeRef}
        globeImageUrl={planet === 'moon'
          ? "https://raw.githubusercontent.com/vasturiano/react-globe.gl/master/example/moon-landing-sites/lunar_surface.jpg"
          : baseLayer === 'satellite'
            ? "https://unpkg.com/three-globe/example/img/earth-night.jpg"
            : "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg"}
        bumpImageUrl={planet === 'moon'
          ? "https://raw.githubusercontent.com/vasturiano/react-globe.gl/master/example/moon-landing-sites/lunar_bumpmap.jpg"
          : "https://unpkg.com/three-globe/example/img/earth-topology.png"}
        backgroundImageUrl="https://unpkg.com/three-globe/example/img/night-sky.png"
        pointsData={globeData}
        pointLat="lat" pointLng="lon" pointColor="color"
        pointAltitude={0.1} pointRadius={0.5}
        pointLabel={(d: any) => `
          <div class="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl font-sans">
            <div class="${planet === 'moon' ? 'text-amber-400' : 'text-emerald-400'} font-bold text-lg mb-1">${d.name}</div>
            <div class="text-slate-400 text-xs uppercase tracking-wider mb-2">${planet === 'moon' ? d.mission : d.country_code}</div>
            <div class="text-slate-300 text-sm">${planet === 'moon' ? d.date : d.site_name}</div>
          </div>`}
        onPointClick={onPointClick}
        atmosphereColor={planet === 'moon' ? "#94a3b8" : "#10b981"}
        atmosphereAltitude={planet === 'moon' ? 0.02 : 0.15}
      />
    );
  }
);
