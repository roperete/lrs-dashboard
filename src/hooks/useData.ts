import { useState, useEffect } from 'react';
import type {
  Simulant, Site, Composition, ChemicalComposition, Reference,
  MineralGroup, SimulantExtra, LunarReference, MineralSourcing, PurchaseInfo
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
  purchaseInfo: PurchaseInfo[];
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
    purchaseInfo: [],
    countriesGeoJson: null,
  });

  useEffect(() => {
    Promise.all([
      fetch(DATA_BASE + 'data.json').then(r => r.ok ? r.json() : {}),
      fetch(DATA_BASE + 'countries.geojson').then(r => r.ok ? r.json() : null),
    ]).then(([data, countriesGeoJson]) => {
      setState({
        loading: false,
        error: null,
        simulants: data.simulants ?? [],
        sites: data.sites ?? [],
        compositions: data.compositions ?? [],
        chemicalCompositions: data.chemical_compositions ?? [],
        references: data.references ?? [],
        mineralGroups: data.mineral_groups ?? [],
        simulantExtra: data.simulant_extra ?? [],
        lunarReference: data.lunar_reference ?? [],
        mineralSourcing: data.mineral_sourcing ?? [],
        purchaseInfo: data.purchase_info ?? [],
        countriesGeoJson: countriesGeoJson?.type ? countriesGeoJson : null,
      });
    }).catch(err => {
      console.error('Data load error:', err);
      setState(prev => ({ ...prev, loading: false, error: err.message }));
    });
  }, []);

  return state;
}
