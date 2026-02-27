import React, { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import { AnimatePresence } from 'motion/react';
import { ChevronRight, Menu } from 'lucide-react';
import L from 'leaflet';
import * as turf from '@turf/turf';

import { useDataContext } from './context/DataContext';
import { useFilters } from './hooks/useFilters';
import { useMapState } from './hooks/useMapState';
import { usePanelState } from './hooks/usePanelState';
import { lunarSites } from './lunarData';
import { clusterByDistance, altitudeToRadius } from './utils/clusterPoints';

import { LoadingScreen } from './components/controls/LoadingScreen';
import { LegendWidget } from './components/controls/LegendWidget';
import { ExportMenu } from './components/controls/ExportMenu';
import { AppHeader } from './components/layout/AppHeader';
import { MapToolbar } from './components/layout/MapToolbar';
import { GlobeView, type GlobeViewHandle, type ClusterPoint } from './components/map/GlobeView';
import { LeafletMap } from './components/map/LeafletMap';
import { Sidebar } from './components/sidebar/Sidebar';
import { SimulantPanel } from './components/panels/SimulantPanel';
import { LunarSitePanel } from './components/panels/LunarSitePanel';
import { ComparisonPanel } from './components/panels/ComparisonPanel';
import { SimulantTable } from './components/table/SimulantTable';

function useIsMobile(breakpoint = 768) {
  const [isMobile, setIsMobile] = useState(window.innerWidth <= breakpoint);
  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth <= breakpoint);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, [breakpoint]);
  return isMobile;
}

export default function App() {
  const data = useDataContext();
  const {
    loading, simulants, compositions, chemicalCompositions, references, mineralGroups,
    lunarReference, compositionBySimulant, chemicalBySimulant, referencesBySimulant,
    mineralGroupsBySimulant, extraBySimulant, siteBySimulant,
    mineralSourcingByMineral, purchaseBySimulant, physicalPropsBySimulant,
  } = data;

  const globeRef = useRef<GlobeViewHandle>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const isMobile = useIsMobile();

  const mapState = useMapState();
  const panelState = usePanelState();
  const filterState = useFilters(simulants, compositions, chemicalCompositions, mineralGroups);

  // Proximity filtering on top of filter results
  const displayedSimulants = useMemo(() => {
    if (!mapState.proximityCenter) return filterState.filteredSimulants;
    return filterState.filteredSimulants.filter(s => {
      const site = siteBySimulant.get(s.simulant_id);
      if (!site || site.lat === null || site.lon === null) return false;
      const from = turf.point([mapState.proximityCenter![1], mapState.proximityCenter![0]]);
      const to = turf.point([site.lon!, site.lat!]);
      return turf.distance(from, to) <= mapState.proximityRadius;
    });
  }, [filterState.filteredSimulants, mapState.proximityCenter, mapState.proximityRadius, siteBySimulant]);

  // Lookup selected entities
  const selectedSimulant = useMemo(() => simulants.find(s => s.simulant_id === panelState.panel1.simulantId) || null, [simulants, panelState.panel1.simulantId]);
  const selectedSimulant2 = useMemo(() => simulants.find(s => s.simulant_id === panelState.panel2.simulantId) || null, [simulants, panelState.panel2.simulantId]);
  const selectedLunarSite = useMemo(() => lunarSites.find(s => s.id === panelState.selectedLunarSiteId) || null, [panelState.selectedLunarSiteId]);

  // Globe altitude state for zoom-reactive clustering
  const [globeAltitude, setGlobeAltitude] = useState(2.5);
  const handleAltitudeChange = useCallback((alt: number) => setGlobeAltitude(alt), []);

  // 3D Earth texture toggle (day/night)
  const [earthTexture, setEarthTexture] = useState<'day' | 'night'>('night');
  const toggleEarthTexture = useCallback(() => setEarthTexture(p => p === 'night' ? 'day' : 'night'), []);

  // Raw Earth points (stable unless data/filters change)
  const rawEarthPoints = useMemo(() => {
    if (mapState.planet !== 'earth') return [];
    return displayedSimulants.map(s => {
      const site = siteBySimulant.get(s.simulant_id);
      return site && site.lat != null && site.lon != null ? {
        simulant_id: s.simulant_id, name: s.name, country_code: s.country_code,
        site_name: site.site_name, lat: site.lat!, lon: site.lon!,
        color: s.type?.toLowerCase().includes('highland') ? '#06b6d4' : '#10b981',
        type: s.type,
      } : null;
    }).filter(Boolean) as any[];
  }, [mapState.planet, displayedSimulants, siteBySimulant]);

  // Globe point data — zoom-reactive clustering
  const { singlePoints, clusterPoints } = useMemo(() => {
    if (mapState.planet === 'moon') {
      const moonPoints = lunarSites.map(s => ({
        id: s.id, name: s.name, mission: s.mission, date: s.date,
        lat: s.lat, lon: s.lng,
        color: s.type === 'Apollo' ? '#f59e0b' : s.type === 'Luna' ? '#ef4444' : '#3b82f6',
      }));
      return { singlePoints: moonPoints, clusterPoints: [] as ClusterPoint[] };
    }
    const radius = altitudeToRadius(mapState.viewMode === 'globe' ? globeAltitude : 0);
    const { singles, clusters } = clusterByDistance(rawEarthPoints, radius);
    return { singlePoints: singles, clusterPoints: clusters };
  }, [mapState.planet, mapState.viewMode, rawEarthPoints, globeAltitude]);

  // Cluster popover state (for 3D globe)
  const [clusterPopover, setClusterPopover] = useState<{
    x: number; y: number; simulants: any[];
  } | null>(null);

  // Close popover on outside click
  useEffect(() => {
    if (!clusterPopover) return;
    const handler = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (!target.closest('[data-cluster-popover]')) setClusterPopover(null);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [clusterPopover]);

  // --- Event handlers ---

  const flyTo = useCallback((lat: number, lng: number, altitude = 1.2) => {
    globeRef.current?.pointOfView({ lat, lng, altitude }, 1000);
  }, []);

  const handleGeocode = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mapState.geocodingQuery.trim()) return;
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(mapState.geocodingQuery)}`);
      const results = await res.json();
      if (results.length > 0) {
        const center: [number, number] = [parseFloat(results[0].lat), parseFloat(results[0].lon)];
        mapState.setMapCenter(center);
        mapState.setMapZoom(12);
        if (mapState.viewMode === 'globe') flyTo(center[0], center[1], 0.4);
      }
    } catch (err) { console.error('Geocoding error:', err); }
  }, [mapState, flyTo]);

  const handleLocate = useCallback(() => {
    navigator.geolocation?.getCurrentPosition((pos) => {
      const center: [number, number] = [pos.coords.latitude, pos.coords.longitude];
      mapState.setMapCenter(center);
      mapState.setMapZoom(14);
      if (mapState.viewMode === 'globe') flyTo(center[0], center[1], 0.4);
    });
  }, [mapState, flyTo]);

  const handleMapClick = useCallback((e: L.LeafletMouseEvent) => {
    if (!mapState.proximityCenter && mapState.drawingMode === 'none') {
      mapState.setProximityCenter([e.latlng.lat, e.latlng.lng]);
      return;
    }
    if (mapState.drawingMode === 'marker') {
      mapState.addCustomMarker(e.latlng.lat, e.latlng.lng);
    } else if (mapState.drawingMode === 'polygon') {
      mapState.addPolygonPoint([e.latlng.lat, e.latlng.lng]);
    }
  }, [mapState]);

  const handleGlobePointClick = useCallback((p: any) => {
    if (mapState.planet === 'moon') {
      panelState.setSelectedLunarSiteId(p.id);
    } else {
      panelState.selectSimulant(p.simulant_id);
    }
    flyTo(p.lat, p.lon || p.lng, 0.8);
  }, [mapState.planet, panelState, flyTo]);

  const handleSimulantClick = useCallback((id: string, lat: number, lon: number) => {
    panelState.selectSimulant(id);
    mapState.setMapCenter([lat, lon]);
    mapState.setMapZoom(10);
    flyTo(lat, lon, 1.2);
  }, [panelState, mapState, flyTo]);

  const handleLunarSiteClick = useCallback((id: string, lat: number, lng: number) => {
    panelState.setSelectedLunarSiteId(id);
    mapState.setMapCenter([lat, lng]);
    mapState.setMapZoom(6);
    flyTo(lat, lng, 1.2);
  }, [panelState, mapState, flyTo]);

  const handlePlanetChange = useCallback((p: 'earth' | 'moon') => {
    mapState.setPlanet(p);
    mapState.setViewMode('globe');
  }, [mapState]);

  const handleSetDrawingMode = useCallback((mode: 'none' | 'marker' | 'polygon') => {
    mapState.setDrawingMode(mode);
    if (mode !== 'polygon') mapState.setTempPolygonPoints([]);
  }, [mapState]);

  if (loading) return <LoadingScreen />;

  return (
    <div className="h-screen w-screen bg-slate-950 overflow-hidden relative font-sans text-slate-200">
      <AppHeader
        planet={mapState.planet} viewMode={mapState.viewMode}
        geocodingQuery={mapState.geocodingQuery} sidebarOpen={isSidebarOpen}
        onPlanetChange={handlePlanetChange}
        onViewModeChange={mapState.setViewMode}
        onGeocodingQueryChange={mapState.setGeocodingQuery}
        onGeocode={handleGeocode}
      />

      {/* Visualization */}
      {mapState.viewMode === 'table' ? (
        <div className={`absolute inset-0 z-0 pt-24 pb-4 transition-[padding] duration-300 ${isSidebarOpen ? 'pl-[21rem]' : 'pl-4'} pr-4`}>
          <div className="h-full bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden">
            <SimulantTable
              simulants={displayedSimulants}
              selectedSimulantId={panelState.panel1.simulantId}
              chemicalBySimulant={chemicalBySimulant}
              physicalPropsBySimulant={physicalPropsBySimulant}
              onSelectSimulant={(id) => panelState.selectSimulant(id)}
            />
          </div>
        </div>
      ) : (
        <div className="absolute inset-0 z-0">
          {mapState.viewMode === 'globe' ? (
            <GlobeView
              ref={globeRef}
              planet={mapState.planet} earthTexture={earthTexture}
              singlePoints={singlePoints} clusterPoints={clusterPoints}
              onPointClick={handleGlobePointClick}
              onClusterClick={(cluster, event) => {
                setClusterPopover({ x: event.clientX, y: event.clientY, simulants: cluster.simulants });
              }}
              onAltitudeChange={handleAltitudeChange}
            />
          ) : (
            <LeafletMap
              planet={mapState.planet}
              mapCenter={mapState.mapCenter} mapZoom={mapState.mapZoom}
              filteredSimulants={displayedSimulants} siteBySimulant={siteBySimulant}
              lunarSites={lunarSites}
              customMarkers={mapState.customMarkers} customPolygons={mapState.customPolygons}
              tempPolygonPoints={mapState.tempPolygonPoints}
              proximityCenter={mapState.proximityCenter} proximityRadius={mapState.proximityRadius}
              onSimulantClick={handleSimulantClick} onLunarSiteClick={handleLunarSiteClick}
              onMapClick={handleMapClick}
            />
          )}
        </div>
      )}

      {/* Cluster popover (3D globe) */}
      {clusterPopover && mapState.viewMode !== 'table' && (
        <div data-cluster-popover
          className="fixed z-[60] bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-xl shadow-2xl p-2 min-w-[220px] max-h-[300px] overflow-y-auto"
          style={{ left: Math.min(clusterPopover.x + 12, window.innerWidth - 240), top: clusterPopover.y - 8 }}
        >
          <div className="text-[10px] text-slate-500 uppercase tracking-wider font-bold px-2 py-1.5 border-b border-slate-800 mb-1">
            {clusterPopover.simulants.length} simulants at this location
          </div>
          {clusterPopover.simulants.map((s: any) => (
            <button key={s.simulant_id}
              className="w-full text-left px-2 py-2 rounded-lg hover:bg-slate-800 transition-colors flex items-center gap-2"
              onClick={() => { handleGlobePointClick(s); setClusterPopover(null); }}>
              <span className="text-emerald-400 font-medium text-sm">{s.name}</span>
              <span className="text-slate-500 text-xs ml-auto">{s.type}</span>
            </button>
          ))}
        </div>
      )}

      {/* Mobile overlay */}
      <AnimatePresence>
        {isSidebarOpen && isMobile && (
          <div onClick={() => setIsSidebarOpen(false)}
            className="fixed inset-0 bg-black/50 z-[45]" />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence>
        {isSidebarOpen && (
          <Sidebar
            planet={mapState.planet}
            searchQuery={filterState.searchQuery}
            onSearchChange={filterState.setSearchQuery}
            filters={filterState.filters}
            filterOptions={filterState.filterOptions}
            setFilter={filterState.setFilter}
            clearAllFilters={filterState.clearAllFilters}
            filteredSimulants={displayedSimulants}
            lunarSites={lunarSites}
            selectedSimulantId={panelState.panel1.simulantId}
            selectedSimulantId2={panelState.panel2.simulantId}
            selectedLunarSiteId={panelState.selectedLunarSiteId}
            onSelectSimulant={(id) => {
              const site = siteBySimulant.get(id);
              if (site && site.lat !== null && site.lon !== null) {
                handleSimulantClick(id, site.lat!, site.lon!);
              } else {
                panelState.selectSimulant(id);
              }
              if (isMobile) setIsSidebarOpen(false);
            }}
            onSelectCompare={(id) => {
              if (panelState.panel2.simulantId === id) {
                panelState.closePanel(2);
              } else {
                panelState.openPanel(2, id);
              }
            }}
            onSelectLunarSite={(id) => {
              const site = lunarSites.find(s => s.id === id);
              if (site) handleLunarSiteClick(id, site.lat, site.lng);
              if (isMobile) setIsSidebarOpen(false);
            }}
            onCompareClick={() => panelState.setShowComparison(true)}
            onClose={() => setIsSidebarOpen(false)}
            proximityCenter={mapState.proximityCenter}
            proximityRadius={mapState.proximityRadius}
            onSetProximityCenter={() => {
              if (mapState.viewMode === 'map') alert('Click on the map to set proximity center');
              else handleLocate();
            }}
            onClearProximityCenter={() => mapState.setProximityCenter(null)}
            onProximityRadiusChange={mapState.setProximityRadius}
            totalCount={simulants.length}
          />
        )}
      </AnimatePresence>

      {/* Sidebar toggle / hamburger */}
      {!isSidebarOpen && (
        <button onClick={() => setIsSidebarOpen(true)}
          className="absolute left-4 top-24 z-[50] p-3 bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-xl text-slate-400 hover:text-emerald-400 transition-all">
          {isMobile ? <Menu size={20} /> : <ChevronRight size={20} />}
        </button>
      )}

      {/* Right toolbar (hidden in table mode) */}
      {mapState.viewMode !== 'table' && (
        <MapToolbar
          planet={mapState.planet} viewMode={mapState.viewMode}
          drawingMode={mapState.drawingMode}
          tempPolygonPointsCount={mapState.tempPolygonPoints.length}
          onToggleEarthTexture={toggleEarthTexture}
          onLocate={handleLocate}
          onSetDrawingMode={handleSetDrawingMode}
          onFinishPolygon={mapState.finishPolygon}
        />
      )}

      {/* Detail panels */}
      <AnimatePresence>
        {selectedSimulant && panelState.panel1.open && (
          <SimulantPanel
            simulant={selectedSimulant}
            compositions={compositionBySimulant.get(selectedSimulant.simulant_id) || []}
            chemicalCompositions={chemicalBySimulant.get(selectedSimulant.simulant_id) || []}
            references={referencesBySimulant.get(selectedSimulant.simulant_id) || []}
            mineralGroups={mineralGroupsBySimulant.get(selectedSimulant.simulant_id) || []}
            extra={extraBySimulant.get(selectedSimulant.simulant_id)}
            lunarReferences={lunarReference}
            physicalProperties={physicalPropsBySimulant.get(selectedSimulant.simulant_id)}
            purchaseInfo={purchaseBySimulant.get(selectedSimulant.simulant_id)}
            mineralSourcingByMineral={mineralSourcingByMineral}
            pinned={panelState.panel1.pinned}
            onClose={() => panelState.closePanel(1)}
            onTogglePin={() => panelState.togglePin(1)}
            onCompare={() => panelState.toggleCompare()}
            compareActive={panelState.compareMode}
          />
        )}
        {selectedLunarSite && (
          <LunarSitePanel site={selectedLunarSite} onClose={() => panelState.setSelectedLunarSiteId(null)} />
        )}
        {panelState.showComparison && selectedSimulant && selectedSimulant2 && (
          <ComparisonPanel
            simulant1={selectedSimulant}
            composition1={compositionBySimulant.get(selectedSimulant.simulant_id) || []}
            chemicalComposition1={chemicalBySimulant.get(selectedSimulant.simulant_id) || []}
            simulant2={selectedSimulant2}
            composition2={compositionBySimulant.get(selectedSimulant2.simulant_id) || []}
            chemicalComposition2={chemicalBySimulant.get(selectedSimulant2.simulant_id) || []}
            onClose={() => panelState.setShowComparison(false)}
          />
        )}
      </AnimatePresence>

      {/* Export + Legend */}
      <div className="absolute bottom-6 right-6 z-[30]">
        <ExportMenu
          currentSimulant={selectedSimulant}
          filteredSimulants={displayedSimulants}
          allSimulants={simulants}
          compositions={compositions}
          chemicalCompositions={chemicalCompositions}
          references={references}
        />
      </div>

      {mapState.viewMode !== 'table' && (
        <LegendWidget planet={mapState.planet} sidebarOpen={isSidebarOpen} />
      )}
    </div>
  );
}
