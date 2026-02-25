import React, { createContext, useContext, useMemo } from 'react';
import { useData, type DataState } from '../hooks/useData';
import type { Composition, ChemicalComposition, Reference, MineralGroup, SimulantExtra, Site } from '../types';

interface DataContextValue extends DataState {
  compositionBySimulant: Map<string, Composition[]>;
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  referencesBySimulant: Map<string, Reference[]>;
  mineralGroupsBySimulant: Map<string, MineralGroup[]>;
  extraBySimulant: Map<string, SimulantExtra>;
  siteBySimulant: Map<string, Site>;
}

const DataCtx = createContext<DataContextValue | null>(null);

function buildGroupMap<T extends { simulant_id: string }>(arr: T[]): Map<string, T[]> {
  const m = new Map<string, T[]>();
  for (const item of arr) {
    const existing = m.get(item.simulant_id);
    if (existing) existing.push(item);
    else m.set(item.simulant_id, [item]);
  }
  return m;
}

export function DataProvider({ children }: { children: React.ReactNode }) {
  const data = useData();

  const compositionBySimulant = useMemo(() => buildGroupMap(data.compositions), [data.compositions]);
  const chemicalBySimulant = useMemo(() => buildGroupMap(data.chemicalCompositions), [data.chemicalCompositions]);
  const referencesBySimulant = useMemo(() => buildGroupMap(data.references), [data.references]);
  const mineralGroupsBySimulant = useMemo(() => buildGroupMap(data.mineralGroups), [data.mineralGroups]);

  const extraBySimulant = useMemo(() => {
    const m = new Map<string, SimulantExtra>();
    for (const ex of data.simulantExtra) m.set(ex.simulant_id, ex);
    return m;
  }, [data.simulantExtra]);

  const siteBySimulant = useMemo(() => {
    const m = new Map<string, Site>();
    for (const s of data.sites) m.set(s.simulant_id, s);
    return m;
  }, [data.sites]);

  const value = useMemo<DataContextValue>(() => ({
    ...data,
    compositionBySimulant,
    chemicalBySimulant,
    referencesBySimulant,
    mineralGroupsBySimulant,
    extraBySimulant,
    siteBySimulant,
  }), [data, compositionBySimulant, chemicalBySimulant, referencesBySimulant, mineralGroupsBySimulant, extraBySimulant, siteBySimulant]);

  return <DataCtx.Provider value={value}>{children}</DataCtx.Provider>;
}

export function useDataContext(): DataContextValue {
  const ctx = useContext(DataCtx);
  if (!ctx) throw new Error('useDataContext must be used within DataProvider');
  return ctx;
}
