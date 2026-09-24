import { useState, useEffect } from 'react';
import type {
  Simulant, Site, Composition, ChemicalComposition, Reference, FigureOfMerit,
  MineralGroup, SimulantExtra, LunarReference, MineralSourcing, PurchaseInfo, PropertySource,
  LunarSite, LunarDocument, LunarSource
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
  lunarSites: LunarSite[];
  lunarDocuments: LunarDocument[];
  lunarSources: LunarSource[];
  mineralSourcing: MineralSourcing[];
  purchaseInfo: PurchaseInfo[];
  propertySources: PropertySource[];
  figuresOfMerit: FigureOfMerit[];
  countriesGeoJson: GeoJSON.FeatureCollection | null;
}

/** public/data/data.json as scripts/export_json.py writes it. Every key is optional so
 *  an older bundle, or a failed fetch, still loads as empty tables. */
interface RawBundle {
  simulants?: Simulant[];
  sites?: Site[];
  compositions?: Composition[];
  chemical_compositions?: ChemicalComposition[];
  references?: Reference[];
  mineral_groups?: MineralGroup[];
  simulant_extra?: SimulantExtra[];
  lunar_reference?: LunarReference[];
  lunar_sites?: LunarSite[];
  lunar_documents?: LunarDocument[];
  lunar_sources?: LunarSource[];
  mineral_sourcing?: MineralSourcing[];
  purchase_info?: PurchaseInfo[];
  property_sources?: PropertySource[];
  figures_of_merit?: FigureOfMerit[];
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
    lunarSites: [],
    lunarDocuments: [],
    lunarSources: [],
    mineralSourcing: [],
    purchaseInfo: [],
    propertySources: [],
    figuresOfMerit: [],
    countriesGeoJson: null,
  });

  useEffect(() => {
    Promise.all([
      fetch(DATA_BASE + 'data.json').then((r): Promise<RawBundle> => r.ok ? r.json() : Promise.resolve({})),
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
        lunarSites: data.lunar_sites ?? [],
        lunarDocuments: data.lunar_documents ?? [],
        lunarSources: data.lunar_sources ?? [],
        mineralSourcing: data.mineral_sourcing ?? [],
        purchaseInfo: data.purchase_info ?? [],
        propertySources: data.property_sources ?? [],
        figuresOfMerit: data.figures_of_merit ?? [],
        countriesGeoJson: countriesGeoJson?.type ? countriesGeoJson : null,
      });
    }).catch(err => {
      console.error('Data load error:', err);
      setState(prev => ({ ...prev, loading: false, error: err.message }));
    });
  }, []);

  return state;
}
