import React, { useEffect } from 'react';
import {
  MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents,
  Polyline, Polygon, Circle,
} from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import type { Simulant, Site, CustomMarker, CustomPolygon, LunarSite } from '../../types';

// Fix Leaflet default icons
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Moon icon for Earth simulant markers
const moonIcon = L.divIcon({
  className: '',
  html: `<div style="width:28px;height:28px;display:flex;align-items:center;justify-content:center;background:rgba(16,185,129,0.15);border:2px solid #10b981;border-radius:50%;box-shadow:0 0 8px rgba(16,185,129,0.4);">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
    </svg>
  </div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -16],
});

// Highlands variant (cyan)
const highlandIcon = L.divIcon({
  className: '',
  html: `<div style="width:28px;height:28px;display:flex;align-items:center;justify-content:center;background:rgba(6,182,212,0.15);border:2px solid #06b6d4;border-radius:50%;box-shadow:0 0 8px rgba(6,182,212,0.4);">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>
    </svg>
  </div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
  popupAnchor: [0, -16],
});

// Lunar lander icon for Moon site markers
const landerIcon = L.divIcon({
  className: '',
  html: `<div style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:rgba(245,158,11,0.15);border:2px solid #f59e0b;border-radius:50%;box-shadow:0 0 10px rgba(245,158,11,0.4);">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M12 2L8 8h8l-4-6z"/>
      <rect x="9" y="8" width="6" height="6" rx="1"/>
      <path d="M7 14l-2 4M17 14l2 4M10 14v4M14 14v4"/>
      <path d="M5 18h14"/>
    </svg>
  </div>`,
  iconSize: [32, 32],
  iconAnchor: [16, 16],
  popupAnchor: [0, -18],
});

// Custom cluster icon creator
function createClusterIcon(cluster: any) {
  const count = cluster.getChildCount();
  const size = count < 10 ? 36 : count < 50 ? 42 : 48;
  return L.divIcon({
    className: '',
    html: `<div style="width:${size}px;height:${size}px;display:flex;align-items:center;justify-content:center;background:rgba(16,185,129,0.25);border:2px solid #10b981;border-radius:50%;box-shadow:0 0 12px rgba(16,185,129,0.5);backdrop-filter:blur(4px);">
      <span style="color:#10b981;font-weight:700;font-size:${size < 42 ? 13 : 15}px;">${count}</span>
    </div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  useEffect(() => { map.setView(center, zoom); }, [map, center, zoom]);
  return null;
}

function MapEvents({ onMapClick }: { onMapClick: (e: L.LeafletMouseEvent) => void }) {
  useMapEvents({ click: onMapClick });
  return null;
}

interface LeafletMapProps {
  planet: 'earth' | 'moon';
  mapCenter: [number, number];
  mapZoom: number;
  filteredSimulants: Simulant[];
  siteBySimulant: Map<string, Site>;
  lunarSites: LunarSite[];
  customMarkers: CustomMarker[];
  customPolygons: CustomPolygon[];
  tempPolygonPoints: [number, number][];
  proximityCenter: [number, number] | null;
  proximityRadius: number;
  onSimulantClick: (id: string, lat: number, lon: number) => void;
  onLunarSiteClick: (id: string, lat: number, lng: number) => void;
  onMapClick: (e: L.LeafletMouseEvent) => void;
}

export function LeafletMap({
  planet, mapCenter, mapZoom,
  filteredSimulants, siteBySimulant, lunarSites,
  customMarkers, customPolygons, tempPolygonPoints,
  proximityCenter, proximityRadius,
  onSimulantClick, onLunarSiteClick, onMapClick,
}: LeafletMapProps) {
  const tileUrl = planet === 'moon'
    ? 'https://cartocdn-gusc.global.ssl.fastly.net/opmbuilder/api/v1/map/named/opm-moon-basemap-v0-1/all/{z}/{x}/{y}.png'
    : 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

  return (
    <MapContainer center={mapCenter} zoom={mapZoom}
      style={{ height: '100%', width: '100%', background: '#020617' }} zoomControl={false}>
      <TileLayer url={tileUrl} attribution={planet === 'moon' ? '&copy; OpenPlanetaryMap' : '&copy; OpenStreetMap'} />
      <MapController center={mapCenter} zoom={mapZoom} />
      <MapEvents onMapClick={onMapClick} />

      {/* Earth simulant markers — clustered with spiderfication */}
      {planet === 'earth' && (
        <MarkerClusterGroup
          iconCreateFunction={createClusterIcon}
          spiderfyOnMaxZoom
          showCoverageOnHover={false}
          maxClusterRadius={40}
          spiderfyDistanceMultiplier={1.5}
          animate
        >
          {filteredSimulants.map(sim => {
            const site = siteBySimulant.get(sim.simulant_id);
            if (!site || site.lat === null || site.lon === null) return null;
            const icon = sim.type?.toLowerCase().includes('highland') ? highlandIcon : moonIcon;
            return (
              <Marker key={sim.simulant_id} position={[site.lat!, site.lon!]} icon={icon}
                eventHandlers={{ click: () => onSimulantClick(sim.simulant_id, site.lat!, site.lon!) }}>
                <Popup className="custom-popup">
                  <div className="text-center">
                    <p className="font-bold text-emerald-400">{sim.name}</p>
                    <p className="text-xs text-slate-400">{sim.type} | {sim.country_code}</p>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MarkerClusterGroup>
      )}

      {/* Moon site markers — lunar lander icons */}
      {planet === 'moon' && lunarSites.map(site => (
        <Marker key={site.id} position={[site.lat, site.lng]} icon={landerIcon}
          eventHandlers={{ click: () => onLunarSiteClick(site.id, site.lat, site.lng) }}>
          <Popup className="custom-popup">
            <div className="text-center">
              <p className="font-bold text-amber-400">{site.mission}</p>
              <p className="text-xs">{site.date}</p>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Custom markers */}
      {customMarkers.map(m => (
        <Marker key={m.id} position={[m.lat, m.lng]}>
          <Popup>{m.label}</Popup>
        </Marker>
      ))}

      {/* Custom polygons */}
      {customPolygons.map(p => (
        <Polygon key={p.id} positions={p.positions} pathOptions={{ color: p.color, fillOpacity: 0.2 }} />
      ))}

      {/* Temp polygon drawing */}
      {tempPolygonPoints.length > 1 && (
        <Polyline positions={tempPolygonPoints} pathOptions={{ color: '#10b981', dashArray: '5 5' }} />
      )}

      {/* Proximity circle */}
      {proximityCenter && (
        <Circle center={proximityCenter} radius={proximityRadius * 1000}
          pathOptions={{ color: '#10b981', fillColor: '#10b981', fillOpacity: 0.1 }} />
      )}
    </MapContainer>
  );
}
