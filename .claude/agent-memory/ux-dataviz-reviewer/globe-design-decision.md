# Globe Co-location: Design Decision Record

## Problem
157 simulants, many with identical lat/lon (same institution).
Current fix: spiral offset by 0.8 degrees (~89 km) — geocorrectly wrong, looks broken.

## Options Evaluated

### A. Altitude Stacking (REJECTED)
Stack co-located points at different pointAltitude values.
Problems:
- Hard to click the "buried" lower points — they are occluded by upper ones
- The altitude dimension is already semantically meaningless here (not used for data)
- On a globe viewed from the side, a vertical stack of 4 points becomes a line,
  with only the topmost point clickable
- Does not scale past 3-4 simulants per location
- Does not communicate "these are co-located" to the user

### B. Cluster rings with zoom-to-expand (CONDITIONALLY GOOD — but react-globe.gl lacks zoom events)
Show a ring/pulse at cluster center, count label, zoom on click to separate.
Problems:
- react-globe.gl has no onZoom event or altitude-change callback
- Cannot reactively re-cluster as user spins/zooms the globe
- Would need polling globeRef.current.pointOfView() to get altitude — fragile
- The globe does NOT separate points by zooming in (unlike Leaflet) because all
  points stay at same geo coords — zooming doesn't help co-located points
VERDICT: Zoom-to-separate does not work on a globe for same-coordinate points.

### C. HTML Overlay Clusters (RECOMMENDED — primary)
Use htmlElementsData to render a cluster badge (count bubble) at the shared location.
On click, open a small popover listing all simulants in that cluster.
Researcher clicks a name in the popover to select that simulant.
Pros:
- Solves the core problem: every simulant is reachable in 2 clicks
- Looks intentional — same pattern as web map clusters everywhere
- No coordinate distortion
- 157 points as HTML elements is fine for performance (react-globe.gl handles it)
- Popover can show simulant name + type, giving researchers the info to pick
Cons:
- Need to implement popover positioning (fixed, near click point; not globe-relative)
- Popover must close on globe drag or outside click

### D. Smart spiral with zoom-dependent offset (REJECTED)
Scale the offset by globe altitude so points spread further when zoomed out.
Problems:
- Still places points at geographically incorrect locations — unacceptable
- Zoom-dependent offset means points jump as user zooms — disorienting
- Does not solve the fundamental issue that points from the same building
  are spread across a 50km radius on the map

### HYBRID RECOMMENDED: C (HTML clusters) + rings for visual affordance
1. Precompute clusters from raw (undistorted) coordinates at load time
2. Single simulants: render as pointsData (performant, native Three.js)
3. Multi-simulant clusters: render as htmlElementsData badge (count bubble)
4. On cluster click: show a popover (DOM overlay, not globe-relative) listing simulants
5. Optionally add a ringsData pulse at cluster locations for visual pop

## Implementation Plan

### Step 1: Cluster precomputation (in globeData useMemo, App.tsx)
Group by exact lat/lon match (not rounded — the current rounding is wrong):
```ts
const exact = new Map<string, any[]>();
for (const p of raw) {
  const key = `${p.lat}:${p.lon}`;
  const g = exact.get(key) || [];
  g.push(p);
  exact.set(key, g);
}
```

### Step 2: Separate pointsData and htmlData
```ts
const singlePoints = [...exact.values()].filter(g => g.length === 1).map(g => g[0]);
const clusters = [...exact.values()].filter(g => g.length > 1).map(g => ({
  lat: g[0].lat, lon: g[0].lon,
  count: g.length,
  simulants: g,
}));
```

### Step 3: GlobeView receives both
```tsx
<Globe
  pointsData={singlePoints}
  // ... existing point props
  htmlElementsData={clusters}
  htmlLat="lat" htmlLng="lon"
  htmlElement={(d) => createClusterBadge(d, onClusterClick)}
/>
```

### Step 4: Cluster badge HTML element
```ts
function createClusterBadge(d: ClusterPoint, onClick: (d: ClusterPoint, event: MouseEvent) => void) {
  const el = document.createElement('div');
  el.style.cssText = `
    width: 36px; height: 36px;
    background: rgba(16,185,129,0.25);
    border: 2px solid #10b981;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    font-weight: 700; font-size: 13px; color: #10b981;
    box-shadow: 0 0 12px rgba(16,185,129,0.4);
    backdrop-filter: blur(2px);
  `;
  el.textContent = String(d.count);
  el.addEventListener('click', (e) => { e.stopPropagation(); onClick(d, e); });
  return el;
}
```

### Step 5: Popover component
A fixed-position DOM overlay (not portal, just absolute inside the globe container).
Position near the click event clientX/clientY.
Lists each simulant with name + type chip.
Clicking a simulant name calls onPointClick with that simulant's data.
Closes on outside click or globe mousedown.

### Step 6: ringsData for visual affordance (optional, low effort)
```tsx
<Globe
  ringsData={clusters}
  ringLat="lat" ringLng="lon"
  ringColor={() => '#10b981'}
  ringMaxRadius={3} ringPropagationSpeed={2} ringRepeatPeriod={800}
/>
```
This adds a subtle pulse at cluster locations — communicates "something is here"
without being distracting.

## Key Constraints to Respect
- Popover must be positioned in screen space (clientX/Y from click event), not
  globe lat/lon space — there is no reliable way to project globe coords to screen
  coords without Three.js raycasting
- The GlobeView component must expose an onClusterClick callback
- The cluster popover state lives in App.tsx (or a new hook), not inside GlobeView
- htmlElementsData elements are recreated when data changes — avoid heavy DOM in the badge
