import { useState, useEffect } from 'react';
import type {
  Simulant, Site, Composition, ChemicalComposition, Reference,
  MineralGroup, SimulantExtra, LunarReference, MineralSourcing
} from '../types';

export interface DataState {
  loading: boolean;
  error: string | null;
  simulants: Simulant[];
  sites: Site[];
  compositions: Composition[];
  chemicalCompositions: ChemicalComposition[];
  references: Reference[];
  mineralGroups: MineralGroup[];
  simulantExtra: SimulantExtra[];
  lunarReference: LunarReference[];
  mineralSourcing: MineralSourcing[];
  countriesGeoJson: GeoJSON.FeatureCollection | null;
}

const DATA_BASE = import.meta.env.BASE_URL + 'data/';

export function useData(): DataState {
  const [state, setState] = useState<DataState>({
    loading: true,
    error: null,
    simulants: [],
    sites: [],
    compositions: [],
    chemicalCompositions: [],
    references: [],
    mineralGroups: [],
    simulantExtra: [],
    lunarReference: [],
    mineralSourcing: [],
    countriesGeoJson: null,
  });

  useEffect(() => {
    const files = [
      'simulant.json', 'site.json', 'composition.json',
      'chemical_composition.json', 'references.json',
      'mineral_groups.json', 'simulant_extra.json',
      'lunar_reference.json', 'mineral_sourcing.json',
      'countries.geojson',
    ];

    Promise.all(files.map(f => fetch(DATA_BASE + f).then(r => r.json())))
      .then(([simulants, sites, compositions, chemicalCompositions, references,
              mineralGroups, simulantExtra, lunarReference, mineralSourcing, countriesGeoJson]) => {
        setState({
          loading: false,
          error: null,
          simulants,
          sites: sites.filter((s: Site) => s.lat !== null && s.lon !== null),
          compositions,
          chemicalCompositions,
          references,
          mineralGroups,
          simulantExtra,
          lunarReference,
          mineralSourcing,
          countriesGeoJson,
        });
      })
      .catch(err => {
        console.error('Data load error:', err);
        setState(prev => ({ ...prev, loading: false, error: err.message }));
      });
  }, []);

  return state;
}
