/**
 * Runs the sidebar's search and filters over the real data bundle. A simulant with an empty
 * field (Lunar90/250/2000 had no type or country in v2.9.17) must not crash the search: the
 * first keystroke threw on `null.toLowerCase()` and blanked the whole page.
 *
 * Run:  npx tsx scripts/check_filters.tsx
 */
import { readFileSync } from 'node:fs';
import { filterSimulantsDynamic, type FilterContext } from '../src/utils/filterSimulants';
import { getCountryDisplay } from '../src/utils/countryUtils';
import { sortSimulants, SORT_KEYS } from '../src/utils/sortSimulants';
import type { Simulant, DynamicFilter } from '../src/types';

const data = JSON.parse(readFileSync(new URL('../public/data/data.json', import.meta.url), 'utf8'));
const simulants: Simulant[] = data.simulants;
const referencesBySimulant = new Map<string, any[]>();
for (const r of data.references) referencesBySimulant.set(r.simulant_id, [...(referencesBySimulant.get(r.simulant_id) ?? []), r]);
const ctx: FilterContext = {
  compositions: data.compositions, chemicalCompositions: data.chemical_compositions, mineralGroups: data.mineral_groups,
  chemicalBySimulant: new Map(), compositionBySimulant: new Map(), referencesBySimulant,
};

let failed = 0;
function check(what: string, fn: () => boolean) {
  let ok = false, err = '';
  try { ok = fn(); } catch (e) { err = ` — threw ${(e as Error).message}`; }
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}${err}`);
  if (!ok) failed++;
}

// every simulant with an empty searchable field, and the search over all of them
const blank = simulants.filter(s => !s.type || !s.country_code || !s.institution).map(s => s.name);
console.log(`simulants with an empty type, country or institution: ${blank.length}`);
for (const q of ['j', 'JSC', 'lunar', 'greenland', 'highland', 'usa', 'zzz-no-match']) {
  check(`search "${q}" runs over all ${simulants.length} simulants`, () => Array.isArray(filterSimulantsDynamic(simulants, [], q, ctx)));
}
check('search "JSC-1A" finds JSC-1A', () => filterSimulantsDynamic(simulants, [], 'JSC-1A', ctx).some(s => s.name === 'JSC-1A'));
check('search "lunar2000" finds Lunar2000', () => filterSimulantsDynamic(simulants, [], 'lunar2000', ctx).some(s => s.name === 'Lunar2000'));

const filters: DynamicFilter[] = [
  { id: 'f1', property: 'type', values: ['Highlands'] } as DynamicFilter,
  { id: 'f2', property: 'country', values: ['EU'] } as DynamicFilter,
  { id: 'f3', property: 'institution', values: ['NASA (all)'] } as DynamicFilter,
  { id: 'f4', property: 'availability', values: ['Available'] } as DynamicFilter,
];
// the Reference filter: 61 references have a title but no citation text
const noText = data.references.filter((r: any) => !r.reference_text).length;
console.log(`references without citation text: ${noText}`);
filters.push({ id: 'f5', property: 'reference', values: ['lunar'] } as DynamicFilter);
check('Reference filter "Zémeny" finds the Lumina products by title', () => {
  const names = filterSimulantsDynamic(simulants, [{ id: 'r', property: 'reference', values: ['luna analog facility'] } as DynamicFilter], '', ctx).map(s => s.name);
  return names.includes('Lunar90') && names.includes('EAC-1');
});
// the table's Country column sorts on getCountryDisplay(country_code)
check('every country, empty or not, has a display name that sorts', () => simulants.every(s => typeof getCountryDisplay(s.country_code).toLowerCase() === 'string'));
// every table sort, both directions, over the real data; empty values last
const sortCtx = { chemicalBySimulant: new Map(data.chemical_compositions.map((c: any) => [c.simulant_id, [c]])),
  compositionBySimulant: new Map(data.compositions.map((c: any) => [c.simulant_id, [c]])), referencesBySimulant };
for (const key of SORT_KEYS) for (const dir of ['asc', 'desc'] as const) {
  check(`sort by ${key} ${dir} keeps all ${simulants.length} rows`, () => sortSimulants(simulants, key, dir, sortCtx as any).length === simulants.length);
}
check('an empty country sorts last in both directions', () => ['asc', 'desc'].every(dir => {
  const out = sortSimulants(simulants, 'country', dir as any, sortCtx as any);
  return !out[0].country_code === false && !out[out.length - 1].country_code;
}));
for (const f of filters) check(`filter ${f.property} runs`, () => Array.isArray(filterSimulantsDynamic(simulants, [f], '', ctx)));
check('search and all filters together run', () => Array.isArray(filterSimulantsDynamic(simulants, filters, 'a', ctx)));

if (failed) { console.log(`${failed} check(s) failed`); process.exit(1); }
console.log('filter check passed');
