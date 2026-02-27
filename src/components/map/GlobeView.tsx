import React, { useRef, useEffect, forwardRef, useImperativeHandle, useCallback } from 'react';
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
  earthTexture: 'day' | 'night';
  singlePoints: any[];
  clusterPoints: ClusterPoint[];
  onPointClick: (point: any) => void;
  onClusterClick: (cluster: ClusterPoint, event: MouseEvent) => void;
  onAltitudeChange?: (altitude: number) => void;
}

function createClusterBadge(d: ClusterPoint, onClick: (d: ClusterPoint, e: MouseEvent) => void, onDblClick: (d: ClusterPoint) => void): HTMLElement {
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
    box-shadow: 0 0 8px rgba(16,185,129,0.25);
    user-select: none;
    transition: box-shadow 0.2s, border-color 0.2s;
    pointer-events: auto;
  `;
  el.textContent = String(d.count);
  el.addEventListener('mouseenter', () => {
    el.style.boxShadow = '0 0 16px rgba(16,185,129,0.5)';
    el.style.borderColor = '#34d399';
  });
  el.addEventListener('mouseleave', () => {
    el.style.boxShadow = '0 0 8px rgba(16,185,129,0.25)';
    el.style.borderColor = '#10b981';
  });
  // Debounce click to distinguish single vs double click
  let clickTimer: ReturnType<typeof setTimeout> | null = null;
  el.addEventListener('click', (e) => {
    e.stopPropagation();
    if (clickTimer) { clearTimeout(clickTimer); clickTimer = null; return; }
    clickTimer = setTimeout(() => { clickTimer = null; onClick(d, e); }, 250);
  });
  el.addEventListener('dblclick', (e) => {
    e.stopPropagation();
    if (clickTimer) { clearTimeout(clickTimer); clickTimer = null; }
    onDblClick(d);
  });
  // Pass wheel events through to the globe for zooming
  el.addEventListener('wheel', (e) => { el.style.pointerEvents = 'none'; requestAnimationFrame(() => { el.style.pointerEvents = 'auto'; }); }, { passive: true });
  return el;
}

export const GlobeView = forwardRef<GlobeViewHandle, GlobeViewProps>(
  ({ planet, earthTexture, singlePoints, clusterPoints, onPointClick, onClusterClick, onAltitudeChange }, ref) => {
    const globeRef = useRef<GlobeMethods>(null);
    const lastAltRef = useRef(0);

    useImperativeHandle(ref, () => ({
      pointOfView: (coords, ms) => globeRef.current?.pointOfView(coords, ms),
    }));

    // Poll altitude from globe controls (no native onZoom event)
    useEffect(() => {
      if (!onAltitudeChange) return;
      const interval = setInterval(() => {
        const pov = globeRef.current?.pointOfView();
        if (pov && Math.abs(pov.altitude - lastAltRef.current) > 0.05) {
          lastAltRef.current = pov.altitude;
          onAltitudeChange(pov.altitude);
        }
      }, 200);
      return () => clearInterval(interval);
    }, [onAltitudeChange]);

    const handleClusterDblClick = useCallback((d: ClusterPoint) => {
      const pov = globeRef.current?.pointOfView();
      const newAlt = Math.max((pov?.altitude || 2) * 0.4, 0.15);
      globeRef.current?.pointOfView({ lat: d.lat, lng: d.lon, altitude: newAlt }, 800);
    }, []);

    const htmlElementAccessor = useCallback((d: any) =>
      createClusterBadge(d, onClusterClick, handleClusterDblClick),
    [onClusterClick, handleClusterDblClick]);

    return (
      <Globe
        ref={globeRef}
        globeImageUrl={planet === 'moon'
          ? "https://raw.githubusercontent.com/vasturiano/react-globe.gl/master/example/moon-landing-sites/lunar_surface.jpg"
          : earthTexture === 'day'
            ? "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
            : "https://unpkg.com/three-globe/example/img/earth-night.jpg"}
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
            <div style="color:${d.color}" class="font-bold text-lg mb-1">${d.name}</div>
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
