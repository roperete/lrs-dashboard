import { useState, useCallback } from 'react';

export function useMapState() {
  const [viewMode, setViewMode] = useState<'globe' | 'map' | 'table'>('globe');
  const [planet, setPlanet] = useState<'earth' | 'moon'>('earth');
  const [mapCenter, setMapCenter] = useState<[number, number]>([20, 0]);
  const [mapZoom, setMapZoom] = useState(2);
  const [geocodingQuery, setGeocodingQuery] = useState('');

  const resetView = useCallback(() => {
    setMapCenter([20, 0]);
    setMapZoom(2);
  }, []);

  return {
    viewMode, setViewMode,
    planet, setPlanet,
    mapCenter, setMapCenter,
    mapZoom, setMapZoom,
    geocodingQuery, setGeocodingQuery,
    resetView,
  };
}
