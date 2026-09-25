import React, { useMemo, useEffect } from 'react';
import { ArrowRightLeft, Moon, FileCheck } from 'lucide-react';
import { PanelShell } from '../ui/PanelShell';
import { Tooltip } from '../ui/Tooltip';
import { SimulantProperties } from './SimulantProperties';
import { PhysicalPropertiesSection } from './PhysicalPropertiesSection';
import { FigureOfMeritSection } from './FigureOfMeritSection';
import { PurchaseSection } from './PurchaseSection';
import { MineralChart } from './MineralChart';
import { ChemicalChart } from './ChemicalChart';
import { ReferencesSection } from './ReferencesSection';
import { DataSourceLine } from './CompositionStatus';
import { downloadSimulantCSV } from '../../utils/csv';
import { referenceNumbers, referenceHoverLabel } from '../../utils/references';
import { LunarSourceList } from '../ui/LunarRefs';
import { EMPTY_CITATIONS, type LunarCitations } from '../../utils/lunarCitations';
import type { Simulant, Composition, ChemicalComposition, Reference, MineralGroup, SimulantExtra, LunarReference, PhysicalProperties, PurchaseInfo, PropertySource, FigureOfMerit } from '../../types';

interface SimulantPanelProps {
  simulant: Simulant;
  compositions: Composition[];
  chemicalCompositions: ChemicalComposition[];
  references: Reference[];
  mineralGroups: MineralGroup[];
  extra?: SimulantExtra;
  lunarReferences: LunarReference[];
  /** Numbered sources of a lunar reference sample's values, shown as [L1], [L2] ... */
  lunarCitationsFor?: (sampleId: string) => LunarCitations;
  physicalProperties?: PhysicalProperties;
  /** property_sources rows of this simulant keyed by field, for the citation superscripts. */
  propertySources?: Map<string, PropertySource>;
  /** This simulant's Figures of Merit. */
  figuresOfMerit?: FigureOfMerit[];
  purchaseInfo?: PurchaseInfo;
  selectedLunarRefMission: string | null;
  /** The reference was suggested from the producer's stated lunar sample, not picked by the user. */
  lunarRefSuggested?: boolean;
  onSelectLunarRef: (mission: string | null) => void;
  onOpenCrossComparison: () => void;
  onClose: () => void;
  /** Scroll to this section when the pane opens or the request changes. */
  focusSection?: 'composition' | 'references' | null;
  onCompare?: () => void;
  compareActive?: boolean;
}

export function SimulantPanel({
  simulant, compositions, chemicalCompositions, references, mineralGroups, extra,
  lunarReferences, lunarCitationsFor, physicalProperties, propertySources, figuresOfMerit = [], purchaseInfo,
  selectedLunarRefMission, lunarRefSuggested, onSelectLunarRef, onOpenCrossComparison,
  onClose, onCompare, compareActive, focusSection,
}: SimulantPanelProps) {
  const lunarRef = lunarReferences.find(r => r.mission === selectedLunarRefMission) || null;
  const lunarCites = lunarRef && lunarCitationsFor ? lunarCitationsFor(lunarRef.sample_id) : EMPTY_CITATIONS;
  // App passes only samples with shown values (utils/lunarRef hasLunarValues)
  const missionsWithChem = lunarReferences;

  useEffect(() => {
    if (!focusSection) return;
    // after the pane's slide-in, so the section is laid out
    const t = setTimeout(() => document.getElementById(`pane-${focusSection}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 350);
    return () => clearTimeout(t);
  }, [focusSection, simulant.simulant_id]);

  // Reference numbers are derived here from the reference list, never stored.
  const refNumbers = useMemo(() => referenceNumbers(references), [references]);
  const refLabel = (referenceId: string) => referenceHoverLabel(references.find(r => r.reference_id === referenceId));
  // Existence line: how many documents on file a reader confirmed to name this simulant.
  const namedIn = references.filter(r => r.names_simulant === 1).length;
  const existenceNote = (
    <Tooltip
      text={namedIn === 0
        ? 'No document on file has been confirmed by a reader to name this exact simulant. Its references may still be awaiting verification.'
        : `${namedIn} of ${references.length} reference${references.length === 1 ? '' : 's'} on file ${namedIn === 1 ? 'was' : 'were'} confirmed by a reader to name this exact simulant.`}
      align="left"
    >
      <span className={`inline-flex items-center gap-1.5 text-xs mt-1 border-b border-dotted ${namedIn === 0 ? 'text-amber-400 border-amber-400/40' : 'text-slate-400 border-slate-600'}`}>
        <FileCheck size={12} aria-hidden />
        named in {namedIn} document{namedIn === 1 ? '' : 's'}
      </span>
    </Tooltip>
  );

  return (
    <PanelShell
      title={simulant.name}
      subtitle={simulant.type || extra?.classification || undefined}
      headerNote={existenceNote}
      accentColor={simulant.type?.toLowerCase().includes('highland') ? 'text-cyan-400' : 'text-emerald-400'}
      onClose={onClose}
      onDownload={() => downloadSimulantCSV(simulant, { compositions, chemicalCompositions, references, propertySources: propertySources ? [...propertySources.values()] : [], figuresOfMerit })}
      onCompare={onCompare}
      compareActive={compareActive}
    >
      {/* Jump links (review #9): the pane is long; these stay at the top while it scrolls */}
      <nav aria-label="Sections" className="sticky -top-6 z-10 -mx-6 mb-4 px-6 py-2 bg-slate-900/95 backdrop-blur border-b border-slate-800 flex flex-wrap gap-x-3 gap-y-1 text-xs">
        {[
          ['properties', 'Properties', !!physicalProperties],
          ['composition', 'Composition', true],
          ['fom', 'FoM', figuresOfMerit.length > 0],
          ['purchase', 'Purchase', true],
          ['about', 'About', true],
          ['references', 'References', true],
        ].filter(([, , show]) => show).map(([id, label]) => (
          <a key={id as string} href={`#pane-${id}`} className="text-slate-300 hover:text-white"
            onClick={(e) => { e.preventDefault(); document.getElementById(`pane-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }}>
            {label}
          </a>
        ))}
      </nav>
      <div className="space-y-8">
        {physicalProperties && (
          <section id="pane-properties" className="scroll-mt-14">
            <PhysicalPropertiesSection
              properties={physicalProperties}
              sources={propertySources}
              refNumber={(referenceId) => refNumbers.get(referenceId)}
              refLabel={refLabel}
            />
          </section>
        )}

        <section id="pane-composition" className="scroll-mt-14 space-y-6">
          {/* Lunar reference selector */}
          {missionsWithChem.length > 0 && (
            <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-3 space-y-2">
              <div className="flex items-center gap-2">
                <Moon size={14} className="text-amber-400" />
                <span className="text-xs font-bold text-amber-400">Compare with a lunar sample</span>
              </div>
              <select
                value={lunarRef?.mission ?? ''}
                onChange={(e) => onSelectLunarRef(e.target.value || null)}
                className="w-full bg-slate-800 border border-slate-700 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
              >
                <option value="">No reference comparison</option>
                {missionsWithChem.map(r => (
                  <option key={r.mission} value={r.mission}>
                    {/* the type as its document words it can run long; the first clause fits a menu */}
                    {[r.mission, r.sample_id, r.landing_site, r.type && `(${r.type.split(';')[0].trim()})`].filter(Boolean).join(' — ')}
                  </option>
                ))}
              </select>
              {lunarRef && (
                <button
                  onClick={onOpenCrossComparison}
                  className="w-full flex items-center justify-center gap-2 py-2 bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 rounded-lg text-xs font-medium text-amber-300 transition-colors"
                >
                  <ArrowRightLeft size={12} />Full comparison
                </button>
              )}
              {lunarRef && lunarRefSuggested && (
                <p className="text-xs text-slate-400">Suggested from the lunar sample the producer says this simulant replicates.</p>
              )}
              {lunarRef && <LunarSourceList citations={lunarCites} prefix="L" title={`Sources for ${lunarRef.mission} ${lunarRef.sample_id}`} />}
            </div>
          )}
  
            <DataSourceLine simulant={simulant} />
          <MineralChart
            compositions={compositions}
            mineralGroups={mineralGroups}
            lunarRef={lunarRef}
            lunarCitations={lunarCites}
            simulantName={simulant.name}
            simulant={simulant}
            references={references}
          />
          <ChemicalChart
            chemicalCompositions={chemicalCompositions}
            lunarRef={lunarRef}
            lunarCitations={lunarCites}
            simulantName={simulant.name}
            simulant={simulant}
            references={references}
          />
        </section>

        {figuresOfMerit.length > 0 && (
          <section id="pane-fom" className="scroll-mt-14">
            <FigureOfMeritSection foms={figuresOfMerit} refNumber={(referenceId) => refNumbers.get(referenceId)} refLabel={refLabel} />
          </section>
        )}

        <section id="pane-purchase" className="scroll-mt-14">
          <PurchaseSection availability={simulant.availability} purchaseInfo={purchaseInfo} />
        </section>

        <section id="pane-about" className="scroll-mt-14">
          <h3 className="text-sm font-semibold text-slate-300 mb-2">About</h3>
          <SimulantProperties simulant={simulant} extra={extra} sources={propertySources}
            refNumber={(referenceId) => refNumbers.get(referenceId)} refLabel={refLabel} />
        </section>

        <section id="pane-references" className="scroll-mt-14">
          <ReferencesSection references={references} simulantName={simulant.name} />
        </section>
      </div>
    </PanelShell>
  );
}
