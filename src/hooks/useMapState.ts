import { useState, useCallback } from 'react';
import type { CustomMarker, CustomPolygon } from '../types';

export function useMapState() {
  const [viewMode, setViewMode] = useState<'globe' | 'map'>('globe');
  const [planet, setPlanet] = useState<'earth' | 'moon'>('earth');
  const [baseLayer, setBaseLayer] = useState<'satellite' | 'streets'>('satellite');
  const [mapCenter, setMapCenter] = useState<[number, number]>([20, 0]);
  const [mapZoom, setMapZoom] = useState(2);
  const [geocodingQuery, setGeocodingQuery] = useState('');
  const [drawingMode, setDrawingMode] = useState<'none' | 'marker' | 'polygon'>('none');
  const [customMarkers, setCustomMarkers] = useState<CustomMarker[]>([]);
  const [customPolygons, setCustomPolygons] = useState<CustomPolygon[]>([]);
  const [tempPolygonPoints, setTempPolygonPoints] = useState<[number, number][]>([]);
  const [proximityCenter, setProximityCenter] = useState<[number, number] | null>(null);
  const [proximityRadius, setProximityRadius] = useState(1000);

  const toggleBaseLayer = useCallback(() => {
    setBaseLayer(prev => prev === 'satellite' ? 'streets' : 'satellite');
  }, []);

  const addCustomMarker = useCallback((lat: number, lng: number) => {
    const marker: CustomMarker = {
      id: Math.random().toString(36).substr(2, 9),
      lat, lng,
      label: `Marker ${Date.now()}`,
    };
    setCustomMarkers(prev => [...prev, marker]);
    setDrawingMode('none');
  }, []);

  const addPolygonPoint = useCallback((point: [number, number]) => {
    setTempPolygonPoints(prev => [...prev, point]);
  }, []);

  const finishPolygon = useCallback(() => {
    setCustomPolygons(prev => [...prev, {
      id: Math.random().toString(36).substr(2, 9),
      positions: tempPolygonPoints,
      color: '#10b981',
    }]);
    setTempPolygonPoints([]);
    setDrawingMode('none');
  }, [tempPolygonPoints]);

  const resetView = useCallback(() => {
    setMapCenter([20, 0]);
    setMapZoom(2);
  }, []);

  return {
    viewMode, setViewMode,
    planet, setPlanet,
    baseLayer, toggleBaseLayer,
    mapCenter, setMapCenter,
    mapZoom, setMapZoom,
    geocodingQuery, setGeocodingQuery,
    drawingMode, setDrawingMode,
    customMarkers, customPolygons,
    tempPolygonPoints, setTempPolygonPoints,
    proximityCenter, setProximityCenter,
    proximityRadius, setProximityRadius,
    addCustomMarker, addPolygonPoint, finishPolygon, resetView,
  };
}
