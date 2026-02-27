import type { Simulant, Composition, ChemicalComposition, MineralGroup, DynamicFilter, Reference } from '../types';
import { isEUMember } from './countryUtils';

export interface FilterContext {
  compositions: Composition[];
  chemicalCompositions: ChemicalComposition[];
  mineralGroups: MineralGroup[];
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  compositionBySimulant: Map<string, Composition[]>;
  referencesBySimulant: Map<string, Reference[]>;
}

export function filterSimulantsDynamic(
  simulants: Simulant[],
  filters: DynamicFilter[],
  searchQuery: string,
  ctx: FilterContext,
): Simulant[] {
  if (filters.length === 0 && !searchQuery) return simulants;

  return simulants.filter(s => {
    // Search query
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const match = s.name.toLowerCase().includes(q) ||
        s.country_code.toLowerCase().includes(q) ||
        s.type.toLowerCase().includes(q) ||
        (s.institution || '').toLowerCase().includes(q);
      if (!match) return false;
    }

    // All dynamic filters (AND logic)
    for (const f of filters) {
      if (f.values.length === 0) continue;

      switch (f.property) {
        case 'type':
          if (!f.values.includes(s.type)) return false;
          break;

        case 'country': {
          const hasEU = f.values.includes('EU');
          const match = f.values.includes(s.country_code) ||
            (hasEU && isEUMember(s.country_code));
          if (!match) return false;
          break;
        }

        case 'institution': {
          const inst = s.institution || '';
          const hasNASA = f.values.includes('NASA (all)');
          const match = f.values.includes(inst) ||
            (hasNASA && inst.toLowerCase().includes('nasa'));
          if (!match) return false;
          break;
        }

        case 'availability':
          if (!f.values.includes(s.availability)) return false;
          break;

        case 'mineral': {
          const detailedMinerals = f.values.filter(m => !m.startsWith('group:'));
          const groupMinerals = f.values.filter(m => m.startsWith('group:')).map(m => m.slice(6));

          const hasDetailedMatch = detailedMinerals.length === 0 ||
            ctx.compositions.some(c =>
              c.simulant_id === s.simulant_id &&
              detailedMinerals.includes(c.component_name) &&
              c.value_pct > 0
            );
          const hasGroupMatch = groupMinerals.length === 0 ||
            ctx.mineralGroups.some(g =>
              g.simulant_id === s.simulant_id &&
              groupMinerals.includes(g.group_name) &&
              g.value_pct > 0
            );
          if (!hasDetailedMatch && !hasGroupMatch) return false;
          break;
        }

        case 'chemical': {
          const hasMatch = ctx.chemicalCompositions.some(c =>
            c.simulant_id === s.simulant_id &&
            f.values.includes(c.component_name) &&
            c.value_wt_pct > 0
          );
          if (!hasMatch) return false;
          break;
        }

        case 'has_chemistry': {
          const has = ctx.chemicalBySimulant.has(s.simulant_id);
          const want = f.values[0] === 'yes';
          if (has !== want) return false;
          break;
        }

        case 'has_mineralogy': {
          const has = ctx.compositionBySimulant.has(s.simulant_id);
          const want = f.values[0] === 'yes';
          if (has !== want) return false;
          break;
        }

        case 'year': {
          const year = typeof s.release_date === 'number' ? s.release_date : null;
          const min = f.values[0] ? parseInt(f.values[0]) : null;
          const max = f.values[1] ? parseInt(f.values[1]) : null;
          if (year == null) return false;
          if (min != null && year < min) return false;
          if (max != null && year > max) return false;
          break;
        }

        case 'reference': {
          const q = (f.values[0] || '').toLowerCase();
          if (!q) break;
          const refs = ctx.referencesBySimulant.get(s.simulant_id);
          if (!refs || refs.length === 0) return false;
          const match = refs.some(r => r.reference_text.toLowerCase().includes(q));
          if (!match) return false;
          break;
        }

        case 'lunar_ref': {
          const q = (f.values[0] || '').toLowerCase();
          if (!q) break;
          if (!(s.lunar_sample_reference || '').toLowerCase().includes(q)) return false;
          break;
        }
      }
    }

    return true;
  });
}
