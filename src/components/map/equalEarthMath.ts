import { geoEqualEarthRaw, type GeoRawProjection } from 'd3-geo';

/**
 * Equal Earth on a sphere of Leaflet's Earth radius, in metres, north and east positive.
 * Data stays in latitude/longitude everywhere; these functions only place it on the 2D map
 * and turn a click on the map back into latitude/longitude.
 */

export const R = 6378137;
const D = Math.PI / 180;
// d3-geo exports the raw projection itself; its type package declares it as a factory.
const raw = geoEqualEarthRaw as unknown as GeoRawProjection;

export function project(lat: number, lng: number): [number, number] {
  const [x, y] = raw(lng * D, lat * D);
  return [x * R, y * R];
}

export function unproject(x: number, y: number): [number, number] {
  const [lambda, phi] = raw.invert!(x / R, y / R);
  return [phi / D, lambda / D];
}

/** Half-width (at the equator) and half-height (at the poles) of the projected map. */
export const X_MAX = project(0, 180)[0];
export const Y_MAX = project(90, 0)[1];

/** Pixel position at a Leaflet zoom level: the map is 256·2^zoom px wide, top-left at (0, 0). */
export function toPixel(lat: number, lng: number, zoom: number): [number, number] {
  const [x, y] = project(lat, lng);
  const scale = 256 * 2 ** zoom, s = 0.5 / X_MAX;
  return [scale * (s * x + 0.5), scale * (-s * y + 0.5 * (Y_MAX / X_MAX))];
}
