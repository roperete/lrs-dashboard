import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { FlaskConical } from 'lucide-react';
import { ToggleButtonGroup } from '../ui/ToggleButtonGroup';
import { CompositionTable } from './CompositionTable';
import { CompositionStatusNotice, statusOf } from './CompositionStatus';
import { referenceNumbers, referenceHoverLabel, rowCitationTooltip } from '../../utils/references';
import type { ChemicalComposition, LunarReference, Simulant, Reference } from '../../types';
import { EMPTY_CITATIONS, type LunarCitations } from '../../utils/lunarCitations';

interface ChemicalChartProps {
  chemicalCompositions: ChemicalComposition[];
  lunarRef?: LunarReference | null;
  /** Sources of the lunar sample's values. */
  lunarCitations?: LunarCitations;
  simulantName: string;
  simulant: Simulant;
  /** This simulant's references, for numbering the documents the rows cite. */
  references?: Reference[];
}

export function ChemicalChart({ chemicalCompositions, lunarRef, lunarCitations = EMPTY_CITATIONS, simulantName, simulant, references = [] }: ChemicalChartProps) {
  const [displayMode, setDisplayMode] = useState<'chart' | 'table'>('table');

  const chemData = useMemo(() =>
    chemicalCompositions
      .filter(c => c.component_type === 'oxide' && c.component_name !== 'sum' && c.value_wt_pct > 0)
      .sort((a, b) => b.value_wt_pct - a.value_wt_pct),
    [chemicalCompositions]);

  const chartData = useMemo(() =>
    chemData.map(c => {
      const entry: Record<string, unknown> = { name: c.component_name, simulant_pct: c.value_wt_pct };
      if (lunarRef?.chemical_composition) {
        entry.lunar_pct = lunarRef.chemical_composition[c.component_name] || 0;
      }
      return entry;
    }),
    [chemData, lunarRef]);

  const refNumbers = useMemo(() => referenceNumbers(references), [references]);
  const refById = useMemo(() => new Map(references.map(r => [r.reference_id, r] as const)), [references]);

  const tableData = useMemo(() =>
    chemData.map(c => ({
      name: c.component_name,
      value: c.value_wt_pct,
      refValue: lunarRef?.chemical_composition?.[c.component_name],
      refValueCites: lunarCitations.cite(`oxide:${c.component_name}`),
      refNumber: c.reference_id ? refNumbers.get(c.reference_id) : undefined,
      refTooltip: rowCitationTooltip(c.value_text, undefined),
        refSource: c.reference_id ? referenceHoverLabel(refById.get(c.reference_id)) : undefined,
    })),
    [chemData, lunarRef, lunarCitations, refNumbers, refById]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FlaskConical size={18} className="text-blue-400" />
          <h3 className="text-base font-semibold text-slate-200">Chemical composition</h3>
        </div>
        {chemData.length > 0 && <ToggleButtonGroup
          options={[{ label: 'Chart', value: 'chart' }, { label: 'Table', value: 'table' }]}
          value={displayMode} onChange={(v) => setDisplayMode(v as 'chart' | 'table')}
        />}
      </div>

      {chemData.length === 0 ? (
        <CompositionStatusNotice status={statusOf(simulant)} kind="chemical" />
      ) : displayMode === 'chart' ? (
        <div className="h-[300px] w-full bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" width={60} stroke="#94a3b8" fontSize={11} tick={{ fill: '#94a3b8' }} />
              <Tooltip
                formatter={(value: number, name: string) => [`${value.toFixed(2)} wt%`, name]}
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <Bar dataKey="simulant_pct" name={simulantName} fill="#3b82f6" radius={[0, 4, 4, 0]}>
                {chartData.map((_, i) => <Cell key={i} fill={i % 2 === 0 ? '#3b82f6' : '#2563eb'} />)}
              </Bar>
              {lunarRef && <Bar dataKey="lunar_pct" name={lunarRef.mission} fill="#fca311" radius={[0, 4, 4, 0]} />}
              {lunarRef && <Legend />}
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <CompositionTable data={tableData} valueLabel="wt%" refLabel={lunarRef?.mission || undefined} partialBelow={90}
          noTotalReason={tableData.some(r => r.name === 'FeO') && tableData.some(r => /^Fe2O3/.test(r.name))
            ? 'The source gives iron twice (FeO and Fe2O3), as two determinations of the same iron; adding both would count it twice.' : undefined} />
      )}
    </div>
  );
}
