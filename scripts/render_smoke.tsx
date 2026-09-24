/**
 * Server-side render check for the citation superscripts.
 *
 * The app has no browser test runner, so this renders the real components with the real
 * bundle (public/data/data.json by default) through react-dom/server and counts the
 * `[n]` marks. Every displayed value that has a property_sources row must carry one, in
 * the right pane and in the main table alike, and every composition row must cite its
 * document on the row itself.
 *
 * Run:  npm run check:render            (or: node_modules/.bin/tsx scripts/render_smoke.tsx [bundle.json])
 * Exits 1 on the first failed expectation.
 */
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { PhysicalPropertiesSection } from '../src/components/panels/PhysicalPropertiesSection';
import { ChemicalChart } from '../src/components/panels/ChemicalChart';
import { MineralChart } from '../src/components/panels/MineralChart';
import { SimulantTable } from '../src/components/table/SimulantTable';
import { FigureOfMeritSection } from '../src/components/panels/FigureOfMeritSection';
import { referenceNumbers } from '../src/utils/references';
import type { ChemicalComposition, Composition, PhysicalProperties, PropertySource, Reference, Simulant } from '../src/types';

const bundlePath = process.argv[2] || fileURLToPath(new URL('../public/data/data.json', import.meta.url));
const d = JSON.parse(readFileSync(bundlePath, 'utf8'));

const PHYSICAL_FIELDS: (keyof PhysicalProperties)[] = [
  'bulk_density', 'cohesion', 'friction_angle', 'specific_gravity', 'density_g_cm3', 'particle_size_d50',
  'particle_size_distribution', 'particle_morphology', 'particle_ruggedness', 'glass_content_percent',
  'nasa_fom_score', 'ti_content_percent', 'ph', 'angle_of_repose', 'particle_size_mean_um',
  'bulk_density_range', 'magnetic_susceptibility',
];
/** The scalar columns the main table shows. */
const TABLE_FIELDS = ['specific_gravity', 'bulk_density', 'particle_size_d50', 'friction_angle', 'cohesion'];

const sups = (html: string) => (html.match(/aria-label="Reference \d+"/g) || []).length;
let failures = 0;
function expect(label: string, got: number, want: number) {
  const ok = got === want;
  if (!ok) failures++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${label}: ${got} superscripts, expected ${want}`);
}

const bySim = <T extends { simulant_id: string }>(rows: T[]) => {
  const m = new Map<string, T[]>();
  for (const r of rows) (m.get(r.simulant_id) ?? m.set(r.simulant_id, []).get(r.simulant_id)!).push(r);
  return m;
};
const refsBy = bySim<Reference>(d.references);
const chemBy = bySim<ChemicalComposition>(d.chemical_compositions);
const minBy = bySim<Composition>(d.compositions);
const sourcesBy = new Map<string, Map<string, PropertySource>>();
for (const p of d.property_sources as PropertySource[]) {
  if (!sourcesBy.has(p.simulant_id)) sourcesBy.set(p.simulant_id, new Map());
  sourcesBy.get(p.simulant_id)!.set(p.field, p);
}

// Right pane: one mark per displayed physical value with a source row.
for (const sim of d.simulants as Simulant[]) {
  const sources = sourcesBy.get(sim.simulant_id);
  if (!sources) continue;
  const props: PhysicalProperties = {};
  for (const k of PHYSICAL_FIELDS) if (sim[k] != null && sim[k] !== '') (props as any)[k] = sim[k];
  const nums = referenceNumbers(refsBy.get(sim.simulant_id) ?? []);
  const html = renderToStaticMarkup(
    <PhysicalPropertiesSection properties={props} sources={sources} refNumber={(id) => nums.get(id)} />);
  const want = Object.keys(props).filter(k => sources.has(k)).length;
  expect(`${sim.name} right pane`, sups(html), want);
}

// Composition tables: every cited row carries its own mark; nothing in the header.
for (const sim of d.simulants as Simulant[]) {
  const refs = refsBy.get(sim.simulant_id) ?? [];
  const chem = chemBy.get(sim.simulant_id) ?? [];
  if (chem.length > 0) {
    const html = renderToStaticMarkup(
      <ChemicalChart chemicalCompositions={chem} lunarRef={null} simulantName={sim.name} simulant={sim} references={refs} />);
    expect(`${sim.name} chemistry rows`, sups(html), chem.filter(c => c.reference_id && c.value_wt_pct > 0).length);
    if (/<th[^>]*>[^<]*<sup/.test(html)) { failures++; console.log(`FAIL ${sim.name} chemistry: citation in the column header`); }
  }
  const mins = minBy.get(sim.simulant_id) ?? [];
  if (mins.length > 0) {
    const html = renderToStaticMarkup(
      <MineralChart compositions={mins} mineralGroups={[]} lunarRef={null} simulantName={sim.name} simulant={sim} references={refs} />);
    expect(`${sim.name} mineral rows`, sups(html), mins.filter(c => c.reference_id && c.value_pct > 0).length);
  }
}

// Figures of Merit: one mark per score.
{
  const bySimFom = bySim<any>(d.figures_of_merit || []);
  for (const sim of d.simulants as Simulant[]) {
    const foms = bySimFom.get(sim.simulant_id) ?? [];
    if (foms.length === 0) continue;
    const nums = referenceNumbers(refsBy.get(sim.simulant_id) ?? []);
    const html = renderToStaticMarkup(<FigureOfMeritSection foms={foms} refNumber={(id) => nums.get(id)} />);
    expect(`${sim.name} figures of merit`, sups(html), foms.length);
  }
}

// Main table: one mark per shown scalar with a source row, across all simulants.
{
  const refNumber = (sid: string, id: string) => referenceNumbers(refsBy.get(sid) ?? []).get(id);
  const html = renderToStaticMarkup(
    <SimulantTable simulants={d.simulants} selectedSimulantId={null}
      chemicalBySimulant={chemBy} compositionBySimulant={minBy} referencesBySimulant={refsBy}
      propertySourcesBySimulant={sourcesBy} refNumber={refNumber}
      onSelectSimulant={() => {}} />);
  let want = 0;
  for (const sim of d.simulants as Simulant[]) {
    const sources = sourcesBy.get(sim.simulant_id);
    if (!sources) continue;
    for (const f of TABLE_FIELDS) if ((sim as any)[f] != null && (sim as any)[f] !== '' && sources.has(f)) want++;
  }
  expect('main table', sups(html), want);
}

console.log(failures === 0 ? 'render check passed' : `render check: ${failures} failure(s)`);
process.exit(failures === 0 ? 0 : 1);
