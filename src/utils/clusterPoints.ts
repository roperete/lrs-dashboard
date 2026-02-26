import type { ClusterPoint } from '../components/map/GlobeView';

/** Haversine distance in degrees (approximate, fast) */
function degDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const dLat = lat2 - lat1;
  const dLon = lon2 - lon1;
  return Math.sqrt(dLat * dLat + dLon * dLon);
}

interface RawPoint {
  lat: number;
  lon: number;
  [key: string]: any;
}

/**
 * Distance-based greedy clustering.
 * Points within `radius` degrees of a cluster centroid get merged.
 */
export function clusterByDistance(
  points: RawPoint[],
  radius: number,
): { singles: RawPoint[]; clusters: ClusterPoint[] } {
  if (radius <= 0) {
    return { singles: points, clusters: [] };
  }

  const used = new Uint8Array(points.length);
  const clusters: ClusterPoint[] = [];
  const singles: RawPoint[] = [];

  for (let i = 0; i < points.length; i++) {
    if (used[i]) continue;
    const group: RawPoint[] = [points[i]];
    used[i] = 1;

    for (let j = i + 1; j < points.length; j++) {
      if (used[j]) continue;
      if (degDistance(points[i].lat, points[i].lon, points[j].lat, points[j].lon) <= radius) {
        group.push(points[j]);
        used[j] = 1;
      }
    }

    if (group.length === 1) {
      singles.push(group[0]);
    } else {
      // Centroid
      const lat = group.reduce((s, p) => s + p.lat, 0) / group.length;
      const lon = group.reduce((s, p) => s + p.lon, 0) / group.length;
      clusters.push({ lat, lon, count: group.length, simulants: group });
    }
  }

  return { singles, clusters };
}

/**
 * Map globe altitude to clustering radius in degrees.
 * altitude ~0.3 (zoomed in)  → radius 0 (no clustering beyond exact overlap)
 * altitude ~1.5 (default)    → radius ~5°
 * altitude ~4.0 (zoomed out) → radius ~20°
 */
export function altitudeToRadius(altitude: number): number {
  if (altitude <= 0.4) return 0.01; // Only cluster exact overlaps
  if (altitude >= 4) return 20;
  // Linear interpolation: 0.4→0.01, 4.0→20
  return 0.01 + ((altitude - 0.4) / 3.6) * 19.99;
}
