import L from 'leaflet';
import { project, unproject, X_MAX, Y_MAX } from './equalEarthMath';

/**
 * The Equal Earth projection (Šavrič, Patterson & Jenny 2018) for the 2D Earth map. It is the
 * projection the UN General Assembly endorsed on 4 September 2026 (resolution A/80/L.104,
 * "Correct the Map") in place of Mercator, which enlarges land towards the poles.
 *
 * Leaflet's own CRS is Web Mercator; this one keeps Leaflet's markers, clustering and popups
 * and changes only how latitude and longitude become map coordinates. Raster tiles exist only
 * in Web Mercator, so the Earth base map is drawn as vectors (ocean, countries, graticule).
 */

export { X_MAX, Y_MAX };

export const EqualEarthProjection: L.Projection = {
  project(latlng: L.LatLng) {
    const [x, y] = project(latlng.lat, latlng.lng);
    return L.point(x, y);
  },
  unproject(point: L.Point) {
    const [lat, lng] = unproject(point.x, point.y);
    return L.latLng(lat, lng);
  },
  bounds: L.bounds([-X_MAX, -Y_MAX], [X_MAX, Y_MAX]),
};

/** Zoom 0 shows the whole width of the map in 256 pixels, as Leaflet's Mercator zoom 0 does
 *  (the same layout as toPixel in equalEarthMath). */
const S = 0.5 / X_MAX;
export const EqualEarthCRS: L.CRS = L.Util.extend({}, L.CRS.Earth, {
  code: 'EqualEarth',
  projection: EqualEarthProjection,
  transformation: new L.Transformation(S, 0.5, -S, 0.5 * (Y_MAX / X_MAX)),
  infinite: false,
});

/** The outline of the projected globe: longitude ±180 from pole to pole. */
export function sphereOutline(step = 1): GeoJSON.Feature<GeoJSON.Polygon> {
  const ring: [number, number][] = [];
  for (let lat = -90; lat <= 90; lat += step) ring.push([-180, lat]);
  for (let lat = 90; lat >= -90; lat -= step) ring.push([180, lat]);
  ring.push(ring[0]);
  return { type: 'Feature', properties: {}, geometry: { type: 'Polygon', coordinates: [ring] } };
}

/** Meridians and parallels every `every` degrees, densified so they curve with the projection. */
export function graticule(every = 30, step = 2): GeoJSON.Feature<GeoJSON.MultiLineString> {
  const lines: [number, number][][] = [];
  for (let lng = -180; lng <= 180; lng += every) {
    const line: [number, number][] = [];
    for (let lat = -90; lat <= 90; lat += step) line.push([lng, lat]);
    lines.push(line);
  }
  for (let lat = -90 + every; lat < 90; lat += every) {
    const line: [number, number][] = [];
    for (let lng = -180; lng <= 180; lng += step) line.push([lng, lat]);
    lines.push(line);
  }
  return { type: 'Feature', properties: {}, geometry: { type: 'MultiLineString', coordinates: lines } };
}
