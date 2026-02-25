import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { FlaskConical } from 'lucide-react';
import { ToggleButtonGroup } from '../ui/ToggleButtonGroup';
import { CompositionTable } from './CompositionTable';
import type { ChemicalComposition, LunarReference } from '../../types';

interface ChemicalChartProps {
  chemicalCompositions: ChemicalComposition[];
  lunarReferences: LunarReference[];
  simulantName: string;
}

export function ChemicalChart({ chemicalCompositions, lunarReferences, simulantName }: ChemicalChartProps) {
  const [displayMode, setDisplayMode] = useState<'chart' | 'table'>('chart');
  const [lunarRefMission, setLunarRefMission] = useState('');

  const chemData = useMemo(() =>
    chemicalCompositions
      .filter(c => c.component_type === 'oxide' && c.component_name !== 'sum' && c.value_wt_pct > 0)
      .sort((a, b) => b.value_wt_pct - a.value_wt_pct),
    [chemicalCompositions]);

  const lunarRef = useMemo(() =>
    lunarReferences.find(r => r.mission === lunarRefMission),
    [lunarReferences, lunarRefMission]);

  const missionsWithChem = useMemo(() =>
    lunarReferences.filter(r => r.chemical_composition && Object.keys(r.chemical_composition).length > 0),
    [lunarReferences]);

  const chartData = useMemo(() =>
    chemData.map(c => {
      const entry: Record<string, unknown> = { name: c.component_name, simulant_pct: c.value_wt_pct };
      if (lunarRef?.chemical_composition) {
        entry.lunar_pct = lunarRef.chemical_composition[c.component_name] || 0;
      }
      return entry;
    }),
    [chemData, lunarRef]);

  const tableData = useMemo(() =>
    chemData.map(c => ({
      name: c.component_name,
      value: c.value_wt_pct,
      refValue: lunarRef?.chemical_composition?.[c.component_name],
    })),
    [chemData, lunarRef]);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FlaskConical size={18} className="text-blue-400" />
          <h3 className="text-lg font-semibold text-slate-200">Chemical Composition</h3>
        </div>
        <ToggleButtonGroup
          options={[{ label: 'Chart', value: 'chart' }, { label: 'Table', value: 'table' }]}
          value={displayMode} onChange={(v) => setDisplayMode(v as 'chart' | 'table')}
        />
      </div>

      {missionsWithChem.length > 0 && (
        <div className="mb-3">
          <select value={lunarRefMission} onChange={(e) => setLunarRefMission(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/50">
            <option value="">No lunar reference comparison</option>
            {missionsWithChem.map(r => <option key={r.mission} value={r.mission}>{r.mission}</option>)}
          </select>
        </div>
      )}

      {chemData.length === 0 ? (
        <div className="bg-slate-800/30 rounded-xl p-8 text-center border border-slate-700/30">
          <p className="text-slate-500 italic">No chemical composition data available</p>
        </div>
      ) : displayMode === 'chart' ? (
        <div className="h-[300px] w-full bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" width={60} stroke="#94a3b8" fontSize={11} tick={{ fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} />
              <Bar dataKey="simulant_pct" name={simulantName} fill="#3b82f6" radius={[0, 4, 4, 0]}>
                {chartData.map((_, i) => <Cell key={i} fill={i % 2 === 0 ? '#3b82f6' : '#2563eb'} />)}
              </Bar>
              {lunarRef && <Bar dataKey="lunar_pct" name={lunarRefMission} fill="#fca311" radius={[0, 4, 4, 0]} />}
              {lunarRef && <Legend />}
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <CompositionTable data={tableData} valueLabel="wt%" refLabel={lunarRefMission || undefined} />
      )}
    </div>
  );
}
