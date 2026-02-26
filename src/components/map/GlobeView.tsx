import React, { useRef, forwardRef, useImperativeHandle, useCallback } from 'react';
import Globe, { GlobeMethods } from 'react-globe.gl';

export interface GlobeViewHandle {
  pointOfView: (coords: { lat: number; lng: number; altitude: number }, ms: number) => void;
}

export interface ClusterPoint {
  lat: number;
  lon: number;
  count: number;
  simulants: any[];
}

interface GlobeViewProps {
  planet: 'earth' | 'moon';
  baseLayer: 'satellite' | 'streets';
  singlePoints: any[];
  clusterPoints: ClusterPoint[];
  onPointClick: (point: any) => void;
  onClusterClick: (cluster: ClusterPoint, event: MouseEvent) => void;
}

function createClusterBadge(d: ClusterPoint, onClick: (d: ClusterPoint, e: MouseEvent) => void): HTMLElement {
  const size = d.count < 5 ? 36 : d.count < 10 ? 42 : 48;
  const el = document.createElement('div');
  el.style.cssText = `
    width: ${size}px; height: ${size}px;
    background: rgba(16,185,129,0.2);
    border: 2px solid #10b981;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    font-weight: 700; font-size: ${size < 42 ? 13 : 15}px; color: #10b981;
    box-shadow: 0 0 12px rgba(16,185,129,0.35);
    user-select: none;
    transition: transform 0.15s, box-shadow 0.15s;
    pointer-events: auto;
  `;
  el.textContent = String(d.count);
  el.addEventListener('mouseenter', () => {
    el.style.transform = 'scale(1.15)';
    el.style.boxShadow = '0 0 20px rgba(16,185,129,0.6)';
  });
  el.addEventListener('mouseleave', () => {
    el.style.transform = 'scale(1)';
    el.style.boxShadow = '0 0 12px rgba(16,185,129,0.35)';
  });
  el.addEventListener('click', (e) => {
    e.stopPropagation();
    onClick(d, e);
  });
  return el;
}

export const GlobeView = forwardRef<GlobeViewHandle, GlobeViewProps>(
  ({ planet, baseLayer, singlePoints, clusterPoints, onPointClick, onClusterClick }, ref) => {
    const globeRef = useRef<GlobeMethods>(null);

    useImperativeHandle(ref, () => ({
      pointOfView: (coords, ms) => globeRef.current?.pointOfView(coords, ms),
    }));

    const htmlElementAccessor = useCallback((d: any) =>
      createClusterBadge(d, onClusterClick),
    [onClusterClick]);

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

        /* Individual points */
        pointsData={singlePoints}
        pointLat="lat" pointLng="lon" pointColor="color"
        pointAltitude={0.06} pointRadius={0.4}
        pointLabel={(d: any) => `
          <div class="bg-slate-900 border border-slate-700 p-3 rounded-lg shadow-xl font-sans">
            <div class="${planet === 'moon' ? 'text-amber-400' : 'text-emerald-400'} font-bold text-lg mb-1">${d.name}</div>
            <div class="text-slate-400 text-xs uppercase tracking-wider mb-2">${planet === 'moon' ? d.mission : d.country_code}</div>
            <div class="text-slate-300 text-sm">${planet === 'moon' ? d.date : d.site_name}</div>
          </div>`}
        onPointClick={onPointClick}

        /* Cluster badges (HTML overlays) */
        htmlElementsData={clusterPoints}
        htmlLat="lat" htmlLng="lon"
        htmlAltitude={0.06}
        htmlElement={htmlElementAccessor}

        /* Pulsing rings on cluster locations */
        ringsData={clusterPoints}
        ringLat="lat" ringLng="lon"
        ringColor={() => () => 'rgba(16,185,129,0.3)'}
        ringMaxRadius={2.5}
        ringPropagationSpeed={1.2}
        ringRepeatPeriod={1400}

        atmosphereColor={planet === 'moon' ? "#94a3b8" : "#10b981"}
        atmosphereAltitude={planet === 'moon' ? 0.02 : 0.15}
      />
    );
  }
);
