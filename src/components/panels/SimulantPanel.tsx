import React from 'react';
import { ArrowRightLeft, Moon } from 'lucide-react';
import { PanelShell } from '../ui/PanelShell';
import { SimulantProperties } from './SimulantProperties';
import { PhysicalPropertiesSection } from './PhysicalPropertiesSection';
import { PurchaseSection } from './PurchaseSection';
import { MineralChart } from './MineralChart';
import { ChemicalChart } from './ChemicalChart';
import { ReferencesSection } from './ReferencesSection';
import { downloadSimulantCSV } from '../../utils/csv';
import type { Simulant, Composition, ChemicalComposition, Reference, MineralGroup, SimulantExtra, LunarReference, PhysicalProperties, PurchaseInfo } from '../../types';

function inferLunarRef(ref: string | null | undefined, lunarRefs: LunarReference[]): string | null {
  if (!ref) return null;
  const lower = ref.toLowerCase();
  if (lower.includes('apollo 11') || lower === '10084') return 'Apollo 11';
  if (lower.includes('apollo 12') || lower === '12070') return 'Apollo 12';
  if (lower.includes('apollo 14') || lower === '14163') return 'Apollo 14';
  if (lower.includes('apollo 15') || lower === '15271') return 'Apollo 15';
  if (lower.includes('apollo 16') || lower === '60501') return 'Apollo 16';
  if (lower.includes('apollo 17') || lower === '71501') return 'Apollo 17';
  if (lower.includes("chang'e") || lower.includes('change') || lower.includes('ce5')) return "Chang'e-5";
  return null;
}

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
  selectedLunarRefMission: string | null;
  onSelectLunarRef: (mission: string | null) => void;
  onOpenCrossComparison: () => void;
  pinned?: boolean;
  onClose: () => void;
  onTogglePin?: () => void;
  onCompare?: () => void;
  compareActive?: boolean;
}

export function SimulantPanel({
  simulant, compositions, chemicalCompositions, references, mineralGroups, extra,
  lunarReferences, physicalProperties, purchaseInfo,
  selectedLunarRefMission, onSelectLunarRef, onOpenCrossComparison,
  pinned, onClose, onTogglePin, onCompare, compareActive,
}: SimulantPanelProps) {
  const lunarRef = lunarReferences.find(r => r.mission === selectedLunarRefMission) || null;
  const missionsWithChem = lunarReferences.filter(r => r.chemical_composition && Object.keys(r.chemical_composition).length > 0);

  // Auto-infer on first render if no selection yet
  const inferred = inferLunarRef(simulant.lunar_sample_reference, lunarReferences);
  if (selectedLunarRefMission === null && inferred) {
    // Schedule for next tick to avoid setState during render
    setTimeout(() => onSelectLunarRef(inferred), 0);
  }

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

        {/* Lunar reference selector */}
        {missionsWithChem.length > 0 && (
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3 space-y-2">
            <div className="flex items-center gap-2">
              <Moon size={14} className="text-amber-400" />
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Compare against lunar reference</span>
            </div>
            <select
              value={selectedLunarRefMission || ''}
              onChange={(e) => onSelectLunarRef(e.target.value || null)}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
            >
              <option value="">No reference comparison</option>
              {missionsWithChem.map(r => (
                <option key={r.mission} value={r.mission}>
                  {r.mission} — {r.landing_site} ({r.type})
                </option>
              ))}
            </select>
            {lunarRef && (
              <button
                onClick={onOpenCrossComparison}
                className="w-full flex items-center justify-center gap-2 py-2 bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 rounded-lg text-xs font-medium text-amber-300 transition-colors"
              >
                <ArrowRightLeft size={12} />Full comparison view
              </button>
            )}
          </div>
        )}

        <MineralChart
          compositions={compositions}
          mineralGroups={mineralGroups}
          lunarRef={lunarRef}
          simulantName={simulant.name}
        />

        <ChemicalChart
          chemicalCompositions={chemicalCompositions}
          lunarRef={lunarRef}
          simulantName={simulant.name}
        />

        <ReferencesSection references={references} simulantName={simulant.name} />
      </div>
    </PanelShell>
  );
}
