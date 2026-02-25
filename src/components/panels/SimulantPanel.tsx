import React from 'react';
import { PanelShell } from '../ui/PanelShell';
import { SimulantProperties } from './SimulantProperties';
import { MineralChart } from './MineralChart';
import { ChemicalChart } from './ChemicalChart';
import { ReferencesSection } from './ReferencesSection';
import { downloadSimulantCSV } from '../../utils/csv';
import type { Simulant, Composition, ChemicalComposition, Reference, MineralGroup, SimulantExtra, LunarReference } from '../../types';

interface SimulantPanelProps {
  simulant: Simulant;
  compositions: Composition[];
  chemicalCompositions: ChemicalComposition[];
  references: Reference[];
  mineralGroups: MineralGroup[];
  extra?: SimulantExtra;
  lunarReferences: LunarReference[];
  pinned?: boolean;
  onClose: () => void;
  onTogglePin?: () => void;
  onCompare?: () => void;
  compareActive?: boolean;
}

export function SimulantPanel({
  simulant, compositions, chemicalCompositions, references, mineralGroups, extra,
  lunarReferences, pinned, onClose, onTogglePin, onCompare, compareActive,
}: SimulantPanelProps) {
  return (
    <PanelShell
      title={simulant.name}
      subtitle={extra?.classification || extra?.replica_of || simulant.type}
      pinned={pinned}
      onClose={onClose}
      onTogglePin={onTogglePin}
      onSearchSources={() => {
        window.open(`https://scholar.google.com/scholar?q=${encodeURIComponent(simulant.name + ' lunar regolith')}`, '_blank');
      }}
      onDownload={() => downloadSimulantCSV(simulant, compositions, chemicalCompositions, references)}
      onCompare={onCompare}
      compareActive={compareActive}
    >
      <div className="space-y-8">
        <SimulantProperties simulant={simulant} extra={extra} />

        <MineralChart
          compositions={compositions}
          mineralGroups={mineralGroups}
          lunarReferences={lunarReferences}
          simulantName={simulant.name}
        />

        <ChemicalChart
          chemicalCompositions={chemicalCompositions}
          lunarReferences={lunarReferences}
          simulantName={simulant.name}
        />

        <ReferencesSection references={references} />
      </div>
    </PanelShell>
  );
}
