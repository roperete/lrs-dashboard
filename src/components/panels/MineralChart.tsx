import React, { useState, useMemo, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { Activity } from 'lucide-react';
import { ToggleButtonGroup } from '../ui/ToggleButtonGroup';
import { CompositionTable } from './CompositionTable';
import { CompositionStatusNotice, statusOf } from './CompositionStatus';
import { referenceNumbers, referenceHoverLabel, rowCitationTooltip } from '../../utils/references';
import type { Composition, MineralGroup, LunarReference, Simulant, Reference } from '../../types';
import { EMPTY_CITATIONS, type LunarCitations } from '../../utils/lunarCitations';

interface MineralChartProps {
  compositions: Composition[];
  mineralGroups: MineralGroup[];
  lunarRef?: LunarReference | null;
  /** Sources of the lunar sample's values. */
  lunarCitations?: LunarCitations;
  simulantName: string;
  simulant: Simulant;
  /** This simulant's references, for numbering the documents the rows cite. */
  references?: Reference[];
}

/** The table's basis as its rows state it ("vol%", "area% (AMICS SEM-EDS)", "wt% (XRD)"): the one
 *  every row names, else a bare "%" with the note that the source leaves it unstated. */
function basisLabel(rows: { value_text?: string | null }[]): string {
  const bases = rows.map(r => {
    const t = r.value_text || '';
    const bracket = t.match(/\[([^\]]+)\]\s*$/);
    if (bracket) return bracket[1];
    const m = t.match(/(?:^|\s|\()((?:vol|wt|area|mol)%[^\]]*|[a-z-]+ (?:modal|normative)[^\]]*|estimated modal[^\]]*|% of [^\]]+)$/i);
    return m ? m[1].replace(/\)$/, '').trim() : null;
  });
  const first = bases[0];
  return first && bases.every(b => b === first) ? first : '% (basis as stated per row)';
}

export function MineralChart({ compositions, mineralGroups, lunarRef, lunarCitations = EMPTY_CITATIONS, simulantName, simulant, references = [] }: MineralChartProps) {
  // Grouped (NASA mineral family) rows are derived data and exist only where a source
  // states them; since the 2026-09 audit most simulants have none. Open on whichever
  // view actually has data, and fall back to the detailed list when groups are absent.
  const [view, setView] = useState<'detailed' | 'groups'>(() =>
    mineralGroups.some(g => g.value_pct > 0) ? 'groups' : 'detailed');
  const [displayMode, setDisplayMode] = useState<'chart' | 'table'>('table');

  const detailedData = useMemo(() =>
    compositions.filter(c => c.value_pct > 0).sort((a, b) => b.value_pct - a.value_pct),
    [compositions]);

  const groupData = useMemo(() =>
    mineralGroups.filter(g => g.value_pct > 0).sort((a, b) => b.value_pct - a.value_pct),
    [mineralGroups]);

  useEffect(() => {
    if (view === 'groups' && groupData.length === 0 && detailedData.length > 0) setView('detailed');
  }, [view, groupData.length, detailedData.length]);

  const chartData = useMemo(() => {
    if (view === 'detailed') {
      return detailedData.map(d => {
        const entry: Record<string, unknown> = { name: d.component_name, simulant_pct: d.value_pct };
        if (lunarRef?.mineral_composition) {
          entry.lunar_pct = lunarRef.mineral_composition[d.component_name] || 0;
        }
        return entry;
      });
    }
    return groupData.map(g => {
      const entry: Record<string, unknown> = { name: g.group_name, simulant_pct: g.value_pct };
      if (lunarRef?.mineral_composition) {
        entry.lunar_pct = lunarRef.mineral_composition[g.group_name] || 0;
      }
      return entry;
    });
  }, [view, detailedData, groupData, lunarRef]);

  const refNumbers = useMemo(() => referenceNumbers(references), [references]);
  const refById = useMemo(() => new Map(references.map(r => [r.reference_id, r] as const)), [references]);

  const tableData = useMemo(() => {
    if (view === 'detailed') {
      return detailedData.map(d => ({
        name: d.component_name,
        value: d.value_pct,
        refValue: lunarRef?.mineral_composition?.[d.component_name],
        refValueCites: lunarCitations.cite(`mineral:${d.component_name}`),
        refNumber: d.reference_id ? refNumbers.get(d.reference_id) : undefined,
        refTooltip: rowCitationTooltip(d.value_text, undefined),
        refSource: d.reference_id ? referenceHoverLabel(refById.get(d.reference_id)) : undefined,
      }));
    }
    // Grouped rows are derived from the detailed list and carry no citation of their own.
    return groupData.map(g => ({
      name: g.group_name,
      value: g.value_pct,
      refValue: lunarRef?.mineral_composition?.[g.group_name],
      refValueCites: lunarCitations.cite(`mineral:${g.group_name}`),
    }));
  }, [view, detailedData, groupData, lunarRef, lunarCitations, refNumbers, refById]);

  const hasData = view === 'detailed' ? detailedData.length > 0 : groupData.length > 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-emerald-400" />
          <h3 className="text-base font-semibold text-slate-200">Mineral composition</h3>
        </div>
        {(detailedData.length > 0 || groupData.length > 0) && <div className="flex items-center gap-2">
          <ToggleButtonGroup
            options={[
              { label: 'Detailed', value: 'detailed' },
              {
                label: 'Groups', value: 'groups',
                disabled: groupData.length === 0,
                title: groupData.length === 0
                  ? 'No grouped (NASA mineral family) breakdown is published for this simulant. Groups are shown only where a source states them.'
                  : 'NASA mineral family grouping, as published by the source',
              },
            ]}
            value={view} onChange={(v) => setView(v as 'detailed' | 'groups')}
          />
          <ToggleButtonGroup
            options={[{ label: 'Chart', value: 'chart' }, { label: 'Table', value: 'table' }]}
            value={displayMode} onChange={(v) => setDisplayMode(v as 'chart' | 'table')}
          />
        </div>}
      </div>

      {!hasData ? (
        <CompositionStatusNotice status={statusOf(simulant)} kind="mineral" />
      ) : displayMode === 'chart' ? (
        <div className="h-[300px] w-full bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" width={110} stroke="#94a3b8" fontSize={11} tick={{ fill: '#94a3b8' }} />
              <Tooltip
                formatter={(value: number, name: string) => [`${value.toFixed(2)}%`, name]}
                contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }}
              />
              <Bar dataKey="simulant_pct" name={simulantName} fill="#10b981" radius={[0, 4, 4, 0]}>
                {chartData.map((_, i) => <Cell key={i} fill={i % 2 === 0 ? '#10b981' : '#059669'} />)}
              </Bar>
              {lunarRef && (
                <Bar dataKey="lunar_pct" name={lunarRef.mission} fill="#fca311" radius={[0, 4, 4, 0]} />
              )}
              {lunarRef && <Legend />}
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <CompositionTable data={tableData} valueLabel={view === 'detailed' ? basisLabel(detailedData) : '%'} refLabel={lunarRef?.mission || undefined} completeFrom={99} />
      )}
    </div>
  );
}
