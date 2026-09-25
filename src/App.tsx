import React, { useState, useMemo, useRef, useCallback, useEffect, lazy, Suspense } from 'react';
import { AnimatePresence } from 'motion/react';


import { useDataContext } from './context/DataContext';
import { useFilters } from './hooks/useFilters';
import { useMapState } from './hooks/useMapState';
import { usePanelState } from './hooks/usePanelState';
import { clusterByDistance, altitudeToRadius } from './utils/clusterPoints';
import type { GlobeViewHandle, ClusterPoint } from './components/map/GlobeView';
import type { Simulant } from './types';

import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { suggestedLunarMission } from './utils/lunarRef';
import { readUrlState, writeUrlState, filtersForUrl, type UrlState } from './hooks/useUrlState';
import { LoadingScreen } from './components/controls/LoadingScreen';
import { LegendWidget } from './components/controls/LegendWidget';
import { ExportMenu } from './components/controls/ExportMenu';
import { AppHeader } from './components/layout/AppHeader';
import { MapToolbar } from './components/layout/MapToolbar';
import { HelpModal } from './components/layout/HelpModal';
import { CompareTray } from './components/controls/CompareTray';
import { Sidebar } from './components/sidebar/Sidebar';
import { SimulantPanel } from './components/panels/SimulantPanel';
import { LunarSitePanel } from './components/panels/LunarSitePanel';
import { SimulantTable } from './components/table/SimulantTable';
import { LunarSampleTable } from './components/table/LunarSampleTable';
import { exportToCSV } from './utils/csv';

// Lazy-loaded heavy components (three.js, leaflet, recharts)
const GlobeView = lazy(() => import('./components/map/GlobeView').then(m => ({ default: m.GlobeView })));
const LeafletMap = lazy(() => import('./components/map/LeafletMap').then(m => ({ default: m.LeafletMap })));
const ComparisonPanel = lazy(() => import('./components/panels/ComparisonPanel').then(m => ({ default: m.ComparisonPanel })));
const CrossComparisonPanel = lazy(() => import('./components/panels/CrossComparisonPanel').then(m => ({ default: m.CrossComparisonPanel })));

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
    mineralSourcingByMineral, purchaseBySimulant, physicalPropsBySimulant, propertySourcesBySimulant,
    fomsBySimulant, refNumber, lunarSites, lunarCitationsFor,
  } = data;

  const globeRef = useRef<GlobeViewHandle>(null);
  // The Find pane is open by default where there is room for it (review #5).
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => window.innerWidth >= 1280);
  const [helpOpen, setHelpOpen] = useState(false);
  // Rotation makes thin points hard to click and ignores reduced-motion settings (review #15): off.
  const [isRotating, setIsRotating] = useState(false);
  const isMobile = useIsMobile();

  // The branded loading screen stays up until the first view is drawn (the globe's texture
  // takes seconds to arrive), for at least 1.5 s so the sponsor is seen, and at most 12 s.
  const [firstViewDrawn, setFirstViewDrawn] = useState(false);
  const [splashMinDone, setSplashMinDone] = useState(false);
  const [splashTimedOut, setSplashTimedOut] = useState(false);
  useEffect(() => {
    const min = setTimeout(() => setSplashMinDone(true), 1500);
    const max = setTimeout(() => setSplashTimedOut(true), 12000);
    return () => { clearTimeout(min); clearTimeout(max); };
  }, []);
  const markViewDrawn = useCallback(() => setFirstViewDrawn(true), []);
  const showSplash = loading || !(splashMinDone && (firstViewDrawn || splashTimedOut));

  const mapState = useMapState();
  // the table needs nothing drawn: it counts as ready as soon as the data is there
  useEffect(() => { if (!loading && mapState.viewMode === 'table') markViewDrawn(); }, [loading, mapState.viewMode, markViewDrawn]);
  const panelState = usePanelState();
  const filterState = useFilters(simulants, compositions, chemicalCompositions, mineralGroups, chemicalBySimulant, compositionBySimulant, referencesBySimulant);

  // The page's state in the address bar (review #13): read once on load, written back as it
  // changes. A new selection is a history entry, so Back returns to the previous one.
  const urlReady = useRef(false);
  const applyUrl = useCallback((u: UrlState) => {
    if (u.planet) mapState.setPlanet(u.planet);
    if (u.view) mapState.setViewMode(u.view);
    filterState.clearAllFilters();
    for (const f of u.filters ?? []) filterState.setFacet(f.property, f.values);
    if (u.q) filterState.setSearchQuery(u.q);
    panelState.setCompareIds(u.cmp ?? []);
    if (u.sim) panelState.selectSimulant(u.sim); else panelState.closePanel();
    panelState.setSelectedLunarSiteId(u.site ?? null);
  }, [mapState, filterState, panelState]);
  useEffect(() => {
    applyUrl(readUrlState());
    urlReady.current = true;
    const onPop = () => applyUrl(readUrlState());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  const lastSelection = useRef('');
  useEffect(() => {
    if (!urlReady.current) return;
    const next = writeUrlState({
      planet: mapState.planet, view: mapState.viewMode,
      sim: panelState.panel1.open ? panelState.panel1.simulantId ?? undefined : undefined,
      cmp: panelState.compareIds, filters: filtersForUrl(filterState.filters), q: filterState.searchQuery || undefined,
      site: panelState.selectedLunarSiteId ?? undefined,
    });
    const selection = `${panelState.panel1.open ? panelState.panel1.simulantId : ''}|${panelState.selectedLunarSiteId ?? ''}`;
    if (next === window.location.search || (next === window.location.pathname && !window.location.search)) { lastSelection.current = selection; return; }
    if (selection !== lastSelection.current) window.history.pushState(null, '', next);
    else window.history.replaceState(null, '', next);
    lastSelection.current = selection;
  }, [mapState.planet, mapState.viewMode, panelState.panel1, panelState.compareIds, panelState.selectedLunarSiteId, filterState.filters, filterState.searchQuery]);

  const displayedSimulants = filterState.filteredSimulants;

  // Lookup selected entities
  const selectedSimulant = useMemo(() => simulants.find(s => s.simulant_id === panelState.panel1.simulantId) || null, [simulants, panelState.panel1.simulantId]);
  const compareSimulants = useMemo(() => panelState.compareIds.map(id => simulants.find(s => s.simulant_id === id)).filter((s): s is Simulant => !!s), [simulants, panelState.compareIds]);
  const selectedLunarSite = useMemo(() => lunarSites.find(s => s.id === panelState.selectedLunarSiteId) || null, [lunarSites, panelState.selectedLunarSiteId]);
  const [programmes, setProgrammes] = useState<string[]>([]);
  const displayedLunarSites = useMemo(() => {
    const q = filterState.searchQuery.trim().toLowerCase();
    return lunarSites.filter(site => (programmes.length === 0 || programmes.includes(site.type))
      && (!q || `${site.name} ${site.mission}`.toLowerCase().includes(q)));
  }, [lunarSites, programmes, filterState.searchQuery]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || helpOpen) return;          // Help closes itself
      if (panelState.showComparison) panelState.setShowComparison(false);
      else if (panelState.showCrossComparison) panelState.setShowCrossComparison(false);
      else if (panelState.panel1.open) panelState.closePanel();
      else if (panelState.selectedLunarSiteId) panelState.setSelectedLunarSiteId(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [helpOpen, panelState]);

  // A detail pane is open on the right (the table narrows and the toolbar moves left of it).
  const paneOpen = (!!selectedSimulant && panelState.panel1.open) || !!selectedLunarSite;

  // The lunar sample to compare with: the user's pick for this simulant, else the one its producer
  // names (a suggestion, labelled as such in the panel).
  const lunarRefPicked = !!selectedSimulant && panelState.lunarRefPick?.simulantId === selectedSimulant.simulant_id;
  const lunarRefMission = lunarRefPicked ? panelState.lunarRefPick!.mission : suggestedLunarMission(selectedSimulant?.lunar_sample_reference);
  const selectedLunarRef = useMemo(() => lunarReference.find(r => r.mission === lunarRefMission) || null, [lunarReference, lunarRefMission]);

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
        color: s.type?.toLowerCase().includes('highland') ? '#94a8be' : s.type?.toLowerCase().includes('mare') ? '#d4915c' : '#9b8e82',
        type: s.type,
      } : null;
    }).filter(Boolean) as any[];
  }, [mapState.planet, displayedSimulants, siteBySimulant]);

  // Globe point data — zoom-reactive clustering
  const { singlePoints, clusterPoints } = useMemo(() => {
    if (mapState.planet === 'moon') {
      const moonPoints = displayedLunarSites.map(s => ({
        id: s.id, name: s.name, mission: s.mission, date: s.date,
        lat: s.lat, lon: s.lng,
        color: s.type === 'Apollo' ? '#f59e0b' : s.type === 'Luna' ? '#ef4444' : s.type === 'Chang-e' ? '#3b82f6' : '#a855f7',
      }));
      return { singlePoints: moonPoints, clusterPoints: [] as ClusterPoint[] };
    }
    const radius = altitudeToRadius(mapState.viewMode === 'globe' ? globeAltitude : 0);
    const { singles, clusters } = clusterByDistance(rawEarthPoints, radius);
    return { singlePoints: singles, clusterPoints: clusters };
  }, [mapState.planet, mapState.viewMode, rawEarthPoints, globeAltitude, displayedLunarSites]);

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

  const handleMapClick = useCallback((_e: any) => {
    // No-op: drawing and proximity features removed
  }, []);

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
    mapState.setMapZoom(Math.max(mapState.mapZoom, 4));
    flyTo(lat, lon, 1.2);
  }, [panelState, mapState, flyTo]);

  const handleLunarSiteClick = useCallback((id: string, lat: number, lng: number) => {
    panelState.setSelectedLunarSiteId(id);
    mapState.setMapCenter([lat, lng]);
    mapState.setMapZoom(Math.max(mapState.mapZoom, 4));
    flyTo(lat, lng, 1.2);
  }, [panelState, mapState, flyTo]);

  // Switching planet keeps the view the user is in (review #14).
  const handlePlanetChange = useCallback((p: 'earth' | 'moon') => {
    mapState.setPlanet(p);
  }, [mapState]);


  const viewName = mapState.viewMode === 'table' ? 'the table'
    : mapState.viewMode === 'map' ? 'the map' : mapState.planet === 'moon' ? 'the Moon' : 'the globe';
  // First child of the root in both returns, so the screen is not remounted when the data arrives.
  const splash = (
    <AnimatePresence>
      {showSplash && <LoadingScreen key="splash" status={loading ? 'Loading the database…' : `Drawing ${viewName}…`} />}
    </AnimatePresence>
  );

  if (loading) return <div className="h-dvh w-screen bg-slate-950 overflow-hidden relative">{splash}</div>;

  return (
    <div className="h-dvh w-screen bg-slate-950 overflow-hidden relative font-sans text-slate-200" aria-busy={showSplash}>
      {splash}
      <AppHeader
        planet={mapState.planet} viewMode={mapState.viewMode}
        sidebarOpen={isSidebarOpen}
        filterCount={filterState.filters.length + (filterState.searchQuery ? 1 : 0)}
        onToggleSidebar={() => setIsSidebarOpen(o => !o)}
        onPlanetChange={handlePlanetChange}
        onViewModeChange={mapState.setViewMode}
        onOpenHelp={() => setHelpOpen(true)}
        exportSlot={mapState.planet === 'earth' ? (
          <ExportMenu
            currentSimulant={selectedSimulant}
            filteredSimulants={displayedSimulants}
            allSimulants={simulants}
            compositions={compositions}
            chemicalCompositions={chemicalCompositions}
            references={references}
            propertySources={data.propertySources}
            figuresOfMerit={data.figuresOfMerit}
          />
        ) : undefined}
      />

      {/* Visualization */}
      {mapState.viewMode === 'table' ? (
        <div className={`absolute inset-x-0 bottom-0 top-14 z-0 pt-4 pb-4 transition-[padding] duration-300 ${isSidebarOpen ? 'sm:pl-[21rem]' : ''} pl-4 ${paneOpen ? 'sm:pr-[466px]' : ''} pr-4 ${panelState.compareIds.length > 0 ? 'pb-20' : ''}`}>
          <div className="h-full bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl overflow-hidden">
            <ErrorBoundary scope="the table" area key={`table-${mapState.planet}`}>
            {mapState.planet === 'moon' ? (
              <LunarSampleTable
                sites={displayedLunarSites}
                selectedSiteId={panelState.selectedLunarSiteId}
                onSelectSite={(id) => panelState.setSelectedLunarSiteId(id)}
                onOpenSources={(id) => {
                  panelState.setSelectedLunarSiteId(id);
                  setTimeout(() => document.getElementById('pane-sources')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 400);
                }}
                citationsFor={lunarCitationsFor}
              />
            ) : (
              <SimulantTable
                simulants={displayedSimulants}
                selectedSimulantId={panelState.panel1.simulantId}
                chemicalBySimulant={chemicalBySimulant}
                compositionBySimulant={compositionBySimulant}
                referencesBySimulant={referencesBySimulant}
                propertySourcesBySimulant={propertySourcesBySimulant}
                refNumber={refNumber}
                onSelectSimulant={(id, section) => panelState.selectSimulant(id, section)}
                compareIds={panelState.compareIds}
                onToggleCompare={panelState.toggleCompare}
                onClearFilters={filterState.clearAllFilters}
              />
            )}
            </ErrorBoundary>
          </div>
        </div>
      ) : (
        <div className="absolute inset-x-0 bottom-0 top-14 z-0">
          <ErrorBoundary area key={`${mapState.viewMode}-${mapState.planet}`} onError={markViewDrawn}
            scope={mapState.viewMode === 'globe' ? 'the 3D globe' : 'the 2D map'}
            hint={mapState.viewMode === 'globe' ? 'Your browser may not be able to draw 3D graphics (WebGL). The 2D map and the table work without it: switch view at the top.' : undefined}>
          <Suspense fallback={<LoadingScreen mode="area" status={`Loading ${viewName}…`} />}>
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
                autoRotate={isRotating}
                onReady={markViewDrawn}
              />
            ) : (
              <LeafletMap
                planet={mapState.planet}
                mapCenter={mapState.mapCenter} mapZoom={mapState.mapZoom}
                filteredSimulants={displayedSimulants} siteBySimulant={siteBySimulant}
                lunarSites={displayedLunarSites}
                countries={data.countriesGeoJson}
                onSimulantClick={handleSimulantClick} onLunarSiteClick={handleLunarSiteClick}
                onMapClick={handleMapClick}
                onReady={markViewDrawn}
              />
            )}
          </Suspense>
          </ErrorBoundary>
        </div>
      )}

      {/* Cluster popover (3D globe) */}
      {clusterPopover && mapState.viewMode !== 'table' && (
        <div data-cluster-popover
          className="fixed z-[60] bg-slate-900/95 backdrop-blur-xl border border-slate-700 rounded-xl shadow-2xl p-2 min-w-[220px] max-h-[300px] overflow-y-auto"
          style={{ left: Math.min(clusterPopover.x + 12, window.innerWidth - 240), top: clusterPopover.y - 8 }}
        >
          <div className="text-[10px] text-slate-400 uppercase tracking-wider font-bold px-2 py-1.5 border-b border-slate-800 mb-1">
            {clusterPopover.simulants.length} simulants at this location
          </div>
          {clusterPopover.simulants.map((s: any) => (
            <button key={s.simulant_id}
              className="w-full text-left px-2 py-2 rounded-lg hover:bg-slate-800 transition-colors flex items-center gap-2"
              onClick={() => { handleGlobePointClick(s); setClusterPopover(null); }}>
              <span className={`font-medium text-sm ${s.type?.toLowerCase().includes('highland') ? 'text-cyan-400' : 'text-emerald-400'}`}>{s.name}</span>
              <span className="text-slate-400 text-xs ml-auto">{s.type}</span>
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
            viewMode={mapState.viewMode}
            searchQuery={filterState.searchQuery}
            onSearchChange={filterState.setSearchQuery}
            filters={filterState.filters}
            filterOptions={filterState.filterOptions}
            onAddFilter={filterState.addFilter}
            onUpdateFilter={filterState.updateFilter}
            onRemoveFilter={filterState.removeFilter}
            clearAllFilters={filterState.clearAllFilters}
            setFacet={filterState.setFacet}
            facetCounts={filterState.facetCounts}
            countWith={filterState.countWith}
            filteredSimulants={displayedSimulants}
            totalCount={simulants.length}
            compareIds={panelState.compareIds}
            onToggleCompare={panelState.toggleCompare}
            selectedSimulantId={panelState.panel1.simulantId}
            onSelectSimulant={(id) => {
              const site = siteBySimulant.get(id);
              if (site && site.lat !== null && site.lon !== null) {
                handleSimulantClick(id, site.lat!, site.lon!);
              } else {
                panelState.selectSimulant(id);
              }
              if (isMobile) setIsSidebarOpen(false);
            }}
            lunarSites={displayedLunarSites}
            allLunarSites={lunarSites}
            programmes={programmes}
            onToggleProgramme={(p) => setProgrammes(cur => cur.includes(p) ? cur.filter(x => x !== p) : [...cur, p])}
            selectedLunarSiteId={panelState.selectedLunarSiteId}
            onSelectLunarSite={(id) => {
              const site = lunarSites.find(s => s.id === id);
              if (site) handleLunarSiteClick(id, site.lat, site.lng);
              if (isMobile) setIsSidebarOpen(false);
            }}
            onClose={() => setIsSidebarOpen(false)}
          />
        )}
      </AnimatePresence>


      {/* Right toolbar (hidden in table mode) */}
      {mapState.viewMode !== 'table' && (
        <MapToolbar
          planet={mapState.planet} viewMode={mapState.viewMode}
          earthTexture={earthTexture}
          onToggleEarthTexture={toggleEarthTexture}
          onZoomIn={() => {
            if (mapState.viewMode === 'globe') {
              setGlobeAltitude(prev => Math.max(0.1, prev * 0.6));
              globeRef.current?.pointOfView({ altitude: globeAltitude * 0.6 }, 300);
            } else {
              mapState.setMapZoom(mapState.mapZoom + 1);
            }
          }}
          onZoomOut={() => {
            if (mapState.viewMode === 'globe') {
              setGlobeAltitude(prev => Math.min(10, prev * 1.6));
              globeRef.current?.pointOfView({ altitude: globeAltitude * 1.6 }, 300);
            } else {
              mapState.setMapZoom(Math.max(1, mapState.mapZoom - 1));
            }
          }}

          onHome={() => {
            // the whole globe, on Earth and the Moon alike
            mapState.setMapCenter([20, 0]);
            mapState.setMapZoom(2);
            flyTo(20, 0, 2.5);
          }}
          isRotating={isRotating}
          onToggleRotate={() => setIsRotating(r => !r)}
          paneOpen={paneOpen}
          geocodingQuery={mapState.geocodingQuery}
          onGeocodingQueryChange={mapState.setGeocodingQuery}
          onGeocode={handleGeocode}
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
            lunarCitationsFor={lunarCitationsFor}
            physicalProperties={physicalPropsBySimulant.get(selectedSimulant.simulant_id)}
            propertySources={propertySourcesBySimulant.get(selectedSimulant.simulant_id)}
            figuresOfMerit={fomsBySimulant.get(selectedSimulant.simulant_id)}
            purchaseInfo={purchaseBySimulant.get(selectedSimulant.simulant_id)}
            selectedLunarRefMission={lunarRefMission}
            lunarRefSuggested={!lunarRefPicked && !!selectedLunarRef}
            onSelectLunarRef={(mission) => panelState.setLunarRefPick({ simulantId: selectedSimulant.simulant_id, mission })}
            onOpenCrossComparison={() => panelState.setShowCrossComparison(true)}
            onClose={panelState.closePanel}
            onCompare={() => panelState.toggleCompare(selectedSimulant.simulant_id)}
            compareActive={panelState.compareIds.includes(selectedSimulant.simulant_id)}
            focusSection={panelState.focusSection}
          />
        )}
        {selectedLunarSite && (
          <LunarSitePanel site={selectedLunarSite} citations={lunarCitationsFor(selectedLunarSite.id)}
            replicas={simulants.filter(sim => new RegExp(`\\b${selectedLunarSite.mission.replace(/[.*+?^${}()|[\]\\']/g, '.?')}\\b`, 'i').test(sim.lunar_sample_reference || ''))}
            onSelectSimulant={(id) => { panelState.setSelectedLunarSiteId(null); mapState.setPlanet('earth'); panelState.selectSimulant(id); }}
            onClose={() => panelState.setSelectedLunarSiteId(null)} />
        )}
        {panelState.showComparison && compareSimulants.length >= 2 && (
          <ErrorBoundary scope="the comparison" compact key="comparison">
          <Suspense fallback={null}>
            <ComparisonPanel
              simulants={compareSimulants}
              compositionBySimulant={compositionBySimulant}
              chemicalBySimulant={chemicalBySimulant}
              referencesBySimulant={referencesBySimulant}
              propertySourcesBySimulant={propertySourcesBySimulant}
              onClose={() => panelState.setShowComparison(false)}
            />
          </Suspense>
          </ErrorBoundary>
        )}
        {panelState.showCrossComparison && selectedSimulant && selectedLunarRef && (
          <ErrorBoundary scope="the lunar comparison" compact key="cross-comparison">
          <Suspense fallback={null}>
            <CrossComparisonPanel
              simulant={selectedSimulant}
              chemicalCompositions={chemicalBySimulant.get(selectedSimulant.simulant_id) || []}
              compositions={compositionBySimulant.get(selectedSimulant.simulant_id) || []}
              mineralGroups={mineralGroupsBySimulant.get(selectedSimulant.simulant_id) || []}
              lunarRef={selectedLunarRef}
              lunarCitations={lunarCitationsFor(selectedLunarRef.sample_id)}
              onClose={() => panelState.setShowCrossComparison(false)}
            />
          </Suspense>
          </ErrorBoundary>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {!panelState.showComparison && (
          <CompareTray
            simulants={compareSimulants}
            onRemove={panelState.toggleCompare}
            onCompare={() => panelState.setShowComparison(true)}
            onExport={() => exportToCSV(compareSimulants, { compositions, chemicalCompositions, references, propertySources: data.propertySources, figuresOfMerit: data.figuresOfMerit }, `lrs_compared_${new Date().toISOString().slice(0, 10)}.csv`)}
            onClear={panelState.clearCompare}
            paneOpen={paneOpen}
          />
        )}
      </AnimatePresence>

      {/* Active filters stay visible when the Find pane is closed (review #5) */}
      {!isSidebarOpen && mapState.planet === 'earth' && (filterState.filters.length > 0 || filterState.searchQuery) && (
        <div className="fixed top-16 left-4 z-[40] flex items-center gap-2 px-3 py-1.5 bg-slate-900/95 border border-emerald-500/40 rounded-full text-xs text-slate-200 shadow-lg">
          <button onClick={() => setIsSidebarOpen(true)} className="hover:text-white">
            {filterState.filters.length + (filterState.searchQuery ? 1 : 0)} filter{filterState.filters.length + (filterState.searchQuery ? 1 : 0) === 1 ? '' : 's'} · {displayedSimulants.length} of {simulants.length}
          </button>
          <button onClick={filterState.clearAllFilters} className="text-emerald-400 hover:text-emerald-300">Clear</button>
        </div>
      )}

      {helpOpen && <HelpModal onClose={() => setHelpOpen(false)} />}

      {mapState.viewMode !== 'table' && (
        <LegendWidget planet={mapState.planet} sidebarOpen={isSidebarOpen} />
      )}
    </div>
  );
}
