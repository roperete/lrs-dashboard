/**
 * Checks that the Equal Earth 2D Earth map does not move anything: the data stays in
 * latitude/longitude and the projection only decides where it is drawn.
 *
 *   1. project() equals the Equal Earth formulas as published (Šavrič et al. 2018), written
 *      out here independently of d3 — catches degrees/radians or lat/lng order mistakes;
 *   2. north is up and east is right (known cities);
 *   3. latitude/longitude → map → latitude/longitude returns the same point (a click on the
 *      map reads back the right coordinates), also near the poles and the antimeridian;
 *   4. the projection is equal-area (what the UN resolution asks for);
 *   5. every simulant site lies in the same country outline before and after projection, so
 *      markers and the country layer cannot drift apart;
 *   6. writes an SVG of the projected map with every site, for a look by eye (--svg <path>).
 *
 * Run:  npx tsx scripts/check_projection.tsx [--svg out.svg]
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { project, unproject, toPixel, X_MAX, Y_MAX, R } from '../src/components/map/equalEarthMath';

let failed = 0;
function check(ok: boolean, what: string) {
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}`);
  if (!ok) failed++;
}

// 1. the published formulas (sphere), independently of d3
const A1 = 1.340264, A2 = -0.081106, A3 = 0.000893, A4 = 0.003796, M = Math.sqrt(3) / 2;
function paper(lat: number, lng: number): [number, number] {
  const phi = lat * Math.PI / 180, lambda = lng * Math.PI / 180;
  const t = Math.asin(M * Math.sin(phi)), t2 = t * t, t6 = t2 * t2 * t2;
  const x = (lambda * Math.cos(t)) / (M * (A1 + 3 * A2 * t2 + t6 * (7 * A3 + 9 * A4 * t2)));
  const y = t * (A1 + A2 * t2 + t6 * (A3 + A4 * t2));
  return [x * R, y * R];
}
let worst = 0;
for (let lat = -90; lat <= 90; lat += 7.5) for (let lng = -180; lng <= 180; lng += 15) {
  const [a, b] = project(lat, lng), [c, d] = paper(lat, lng);
  worst = Math.max(worst, Math.hypot(a - c, b - d));
}
check(worst < 1, `matches the published formulas everywhere (largest difference ${worst.toExponential(1)} m)`);

// 2. orientation
const [px, py] = project(48.85, 2.35), [sx, sy] = project(-33.87, 151.21), [bx, by] = project(-34.6, -58.38);
check(px > 0 && py > 0, 'Paris is north and east of (0, 0)');
check(sx > 0 && sy < 0, 'Sydney is south and east');
check(bx < 0 && by < 0, 'Buenos Aires is south and west');
check(toPixel(60, 0, 3)[1] < toPixel(0, 0, 3)[1] && toPixel(0, 90, 3)[0] > toPixel(0, 0, 3)[0], 'on screen, north is up and east is right');

// 3. round trip
for (const [lat, lng] of [[0, 0], [48.85, 2.35], [-33.87, 151.21], [89.99, 179.99], [-89.99, -179.99], [66.544, -52.3085], [28.6, -17.9]]) {
  const [la, ln] = unproject(...project(lat, lng));
  check(Math.abs(la - lat) < 1e-7 && Math.abs(ln - lng) < 1e-7, `round trip ${lat}, ${lng}`);
}
const [w] = toPixel(0, -180, 0), [e] = toPixel(0, 180, 0), [, n] = toPixel(90, 0, 0);
check(Math.abs(w) < 1e-9 && Math.abs(e - 256) < 1e-9 && Math.abs(n) < 1e-9, 'zoom 0 is 256 px wide with the north pole at the top edge');

// 4. equal area: a 1°×1° cell has its true area at every latitude
for (const lat of [0, 30, 60, 80]) {
  const p = (a: number, b: number) => project(a, b);
  const area = (() => { // shoelace over the projected cell
    const pts = [p(lat, 0), p(lat, 1), p(lat + 1, 1), p(lat + 1, 0)];
    return Math.abs(pts.reduce((s, [x1, y1], i) => { const [x2, y2] = pts[(i + 1) % 4]; return s + x1 * y2 - x2 * y1; }, 0) / 2);
  })();
  const truth = (Math.PI / 180) * R * R * (Math.sin((lat + 1) * Math.PI / 180) - Math.sin(lat * Math.PI / 180));
  check(Math.abs(area / truth - 1) < 0.002, `equal area at ${lat}°N (projected/true ${(area / truth).toFixed(4)})`);
}
check(X_MAX > 1.7e7 && Y_MAX > 8.3e6, `extent ±${(X_MAX / 1e3).toFixed(0)} km × ±${(Y_MAX / 1e3).toFixed(0)} km`);

// A point off the map (a window wider or taller than the map at low zoom) must still turn into
// a real place: the nearest point on the outline. v2.9.19-21 returned longitudes like -3857°,
// the visible bounds missed every pin, and the 2D map showed none until zoomed in.
{
  let bad: string[] = [];
  for (const fx of [-2, -1.3, -1.01, 1.01, 1.3, 2]) for (const fy of [-2, -1.2, -1.01, 0, 0.5, 1.01, 1.2, 2]) {
    const [lat, lng] = unproject(fx * X_MAX, fy * Y_MAX);
    if (!(Math.abs(lat) <= 90 && Math.abs(lng) <= 180)) bad.push(`(${fx}, ${fy}) -> ${lat.toFixed(1)}, ${lng.toFixed(1)}`);
  }
  const [la, ln] = unproject(1.5 * X_MAX, 0);
  check(bad.length === 0 && Math.abs(la) < 1e-9 && Math.abs(ln - 180) < 1e-9,
    `points off the map fall on its edge${bad.length ? ': ' + bad.slice(0, 3).join('; ') : ''}`);
  const [ta, tn] = unproject(0.2 * X_MAX, 1.5 * Y_MAX);
  check(Math.abs(ta - 90) < 1e-9 && Math.abs(tn) <= 180, 'above the top edge is the north pole');
}

// 5. every site stays in the same country outline
type Ring = [number, number][];
const geo = JSON.parse(readFileSync(new URL('../public/data/countries.geojson', import.meta.url), 'utf8'));
const data = JSON.parse(readFileSync(new URL('../public/data/data.json', import.meta.url), 'utf8'));
const countries = geo.features.map((f: any) => ({
  name: f.properties.admin || f.properties.name || f.properties.sovereignt,
  polys: (f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates) as Ring[][],
}));
const inside = (x: number, y: number, ring: Ring) => {
  let c = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
};
const inPoly = (x: number, y: number, poly: Ring[]) => inside(x, y, poly[0]) && !poly.slice(1).some(h => inside(x, y, h));
const projected = countries.map((c: any) => ({ ...c, polys: c.polys.map((p: Ring[]) => p.map(r => r.map(([lng, lat]) => project(lat, lng)))) }));
const containing = (list: any[], x: number, y: number) => list.find(c => c.polys.some((p: Ring[]) => inPoly(x, y, p)))?.name ?? 'sea';
const sites = data.sites.filter((s: any) => s.lat != null && s.lon != null);
let same = 0; const moved: string[] = [];
for (const s of sites) {
  const before = containing(countries, s.lon, s.lat);
  const after = containing(projected, ...project(s.lat, s.lon));
  if (before === after) same++; else moved.push(`${s.site_name}: ${before} → ${after}`);
}
check(moved.length === 0, `all ${sites.length} simulant sites lie in the same outline before and after projection (${same} same)`);
moved.slice(0, 10).forEach(m => console.log('     ', m));

// 6. picture
const svgAt = process.argv.indexOf('--svg');
if (svgAt > 0) {
  const Z = 2, px2 = (lat: number, lng: number) => toPixel(lat, lng, Z).map(v => v.toFixed(1)).join(',');
  const outline: string[] = [];
  for (let lat = -90; lat <= 90; lat++) outline.push(px2(lat, -180));
  for (let lat = 90; lat >= -90; lat--) outline.push(px2(lat, 180));
  const paths = countries.flatMap((c: any) => c.polys.map((p: Ring[]) => p.map(r => 'M' + r.map(([lng, lat]) => px2(lat, lng)).join('L') + 'Z').join('')));
  const W = 256 * 2 ** Z, H = W * (Y_MAX / X_MAX);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H.toFixed(0)}" style="background:#020617">
<polygon points="${outline.join(' ')}" fill="#0b1f3a" stroke="#1e3a5f"/>
${paths.map((d: string) => `<path d="${d}" fill="#1e293b" stroke="#475569" stroke-width="0.6"/>`).join('\n')}
${sites.map((s: any) => { const [x, y] = toPixel(s.lat, s.lon, Z); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.5" fill="#10b981" stroke="#fff" stroke-width="0.8"/>`; }).join('\n')}
</svg>`;
  writeFileSync(process.argv[svgAt + 1], svg);
  console.log(`map written to ${process.argv[svgAt + 1]}`);
}

if (failed) { console.log(`${failed} check(s) failed`); process.exit(1); }
console.log('projection check passed');
