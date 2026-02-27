import React from 'react';
import { PanelShell } from '../ui/PanelShell';
import { SimulantProperties } from './SimulantProperties';
import { PhysicalPropertiesSection } from './PhysicalPropertiesSection';
import { PurchaseSection } from './PurchaseSection';
import { MineralChart } from './MineralChart';
import { ChemicalChart } from './ChemicalChart';
import { ReferencesSection } from './ReferencesSection';
import { downloadSimulantCSV } from '../../utils/csv';
import type { Simulant, Composition, ChemicalComposition, Reference, MineralGroup, SimulantExtra, LunarReference, PhysicalProperties, PurchaseInfo } from '../../types';

interface SimulantPanelProps {
  simulant: Simulant;
  compositions: Composition[];
  chemicalCompositions: ChemicalComposition[];
  references: Reference[];
  mineralGroups: MineralGroup[];
  extra?: SimulantExtra;
  lunarReferences: LunarReference[];
  physicalProperties?: PhysicalProperties;
  purchaseInfo?: PurchaseInfo;
  pinned?: boolean;
  onClose: () => void;
  onTogglePin?: () => void;
  onCompare?: () => void;
  compareActive?: boolean;
}

export function SimulantPanel({
  simulant, compositions, chemicalCompositions, references, mineralGroups, extra,
  lunarReferences, physicalProperties, purchaseInfo,
  pinned, onClose, onTogglePin, onCompare, compareActive,
}: SimulantPanelProps) {
  return (
    <PanelShell
      title={simulant.name}
      subtitle={extra?.classification || extra?.replica_of || simulant.type}
      accentColor={simulant.type?.toLowerCase().includes('highland') ? 'text-cyan-400' : 'text-emerald-400'}
      pinned={pinned}
      onClose={onClose}
      onTogglePin={onTogglePin}
      onDownload={() => downloadSimulantCSV(simulant, compositions, chemicalCompositions, references)}
      onCompare={onCompare}
      compareActive={compareActive}
    >
      <div className="space-y-8">
        <SimulantProperties simulant={simulant} extra={extra} />

        {physicalProperties && <PhysicalPropertiesSection properties={physicalProperties} />}

        <PurchaseSection availability={simulant.availability} purchaseInfo={purchaseInfo} />

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

        <ReferencesSection references={references} simulantName={simulant.name} />
      </div>
    </PanelShell>
  );
}
