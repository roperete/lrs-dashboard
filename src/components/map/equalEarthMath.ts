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
  // A point off the map (at low zoom the window is wider and taller than the map) becomes the
  // nearest point on the outline at the same height, so it is still a real place. Inverted
  // as it is, it gives longitudes like -3857°, and Leaflet's visible bounds then miss every pin.
  const yc = Math.max(-Y_MAX, Math.min(Y_MAX, y));
  const rowPhi = raw.invert!(0, yc / R)[1];
  const xEdge = raw(Math.PI, rowPhi)[0] * R;
  const [lambda, phi] = raw.invert!(Math.max(-xEdge, Math.min(xEdge, x)) / R, yc / R);
  return [Math.max(-90, Math.min(90, phi / D)), Math.max(-180, Math.min(180, lambda / D))];
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
