import React, { createContext, useContext, useMemo } from 'react';
import { useData, type DataState } from '../hooks/useData';
import type { Composition, ChemicalComposition, Reference, MineralGroup, SimulantExtra, Site, MineralSourcing, PurchaseInfo, PhysicalProperties } from '../types';

interface DataContextValue extends DataState {
  compositionBySimulant: Map<string, Composition[]>;
  chemicalBySimulant: Map<string, ChemicalComposition[]>;
  referencesBySimulant: Map<string, Reference[]>;
  mineralGroupsBySimulant: Map<string, MineralGroup[]>;
  extraBySimulant: Map<string, SimulantExtra>;
  siteBySimulant: Map<string, Site>;
  mineralSourcingByMineral: Map<string, MineralSourcing>;
  purchaseBySimulant: Map<string, PurchaseInfo>;
  physicalPropsBySimulant: Map<string, PhysicalProperties>;
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

  const mineralSourcingByMineral = useMemo(() => {
    const m = new Map<string, MineralSourcing>();
    for (const ms of data.mineralSourcing) m.set(ms.mineral_name?.toLowerCase(), ms);
    return m;
  }, [data.mineralSourcing]);

  const purchaseBySimulant = useMemo(() => {
    const m = new Map<string, PurchaseInfo>();
    for (const p of data.purchaseInfo) m.set(p.simulant_id, p);
    return m;
  }, [data.purchaseInfo]);

  const physicalPropsBySimulant = useMemo(() => {
    const m = new Map<string, PhysicalProperties>();
    for (const sim of data.simulants) {
      const props: PhysicalProperties = {};
      if (sim.bulk_density != null) props.bulk_density = Number(sim.bulk_density) || undefined;
      if (sim.cohesion != null) props.cohesion = parseFloat(String(sim.cohesion)) || undefined;
      if (sim.friction_angle != null) props.friction_angle = parseFloat(String(sim.friction_angle)) || undefined;
      if (sim.specific_gravity != null) props.specific_gravity = Number(sim.specific_gravity) || undefined;
      if (sim.density_g_cm3 != null) props.density_g_cm3 = Number(sim.density_g_cm3) || undefined;
      if (sim.particle_size_d50 != null) props.particle_size_d50 = Number(sim.particle_size_d50) || undefined;
      if (sim.particle_size_distribution != null) props.particle_size_distribution = String(sim.particle_size_distribution);
      if (sim.particle_morphology != null) props.particle_morphology = String(sim.particle_morphology);
      if (sim.particle_ruggedness != null) props.particle_ruggedness = String(sim.particle_ruggedness);
      if (sim.glass_content_percent != null) props.glass_content_percent = Number(sim.glass_content_percent) || undefined;
      if (sim.nasa_fom_score != null) props.nasa_fom_score = Number(sim.nasa_fom_score) || undefined;
      if (sim.ti_content_percent != null) props.ti_content_percent = Number(sim.ti_content_percent) || undefined;
      if (Object.keys(props).length > 0) m.set(sim.simulant_id, props);
    }
    return m;
  }, [data.simulants]);

  const value = useMemo<DataContextValue>(() => ({
    ...data,
    compositionBySimulant,
    chemicalBySimulant,
    referencesBySimulant,
    mineralGroupsBySimulant,
    extraBySimulant,
    siteBySimulant,
    mineralSourcingByMineral,
    purchaseBySimulant,
    physicalPropsBySimulant,
  }), [data, compositionBySimulant, chemicalBySimulant, referencesBySimulant, mineralGroupsBySimulant, extraBySimulant, siteBySimulant, mineralSourcingByMineral, purchaseBySimulant, physicalPropsBySimulant]);

  return <DataCtx.Provider value={value}>{children}</DataCtx.Provider>;
}

export function useDataContext(): DataContextValue {
  const ctx = useContext(DataCtx);
  if (!ctx) throw new Error('useDataContext must be used within DataProvider');
  return ctx;
}
