import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, Cell } from 'recharts';
import { Activity } from 'lucide-react';
import { ToggleButtonGroup } from '../ui/ToggleButtonGroup';
import { CompositionTable } from './CompositionTable';
import type { Composition, MineralGroup, LunarReference } from '../../types';

interface MineralChartProps {
  compositions: Composition[];
  mineralGroups: MineralGroup[];
  lunarReferences: LunarReference[];
  simulantName: string;
}

export function MineralChart({ compositions, mineralGroups, lunarReferences, simulantName }: MineralChartProps) {
  const [view, setView] = useState<'detailed' | 'groups'>('detailed');
  const [displayMode, setDisplayMode] = useState<'chart' | 'table'>('table');
  const [lunarRefMission, setLunarRefMission] = useState('');

  const detailedData = useMemo(() =>
    compositions.filter(c => c.value_pct > 0).sort((a, b) => b.value_pct - a.value_pct),
    [compositions]);

  const groupData = useMemo(() =>
    mineralGroups.filter(g => g.value_pct > 0).sort((a, b) => b.value_pct - a.value_pct),
    [mineralGroups]);

  const lunarRef = useMemo(() =>
    lunarReferences.find(r => r.mission === lunarRefMission),
    [lunarReferences, lunarRefMission]);

  const missionsWithMinerals = useMemo(() =>
    lunarReferences.filter(r => r.mineral_composition && Object.keys(r.mineral_composition).length > 0),
    [lunarReferences]);

  const chartData = useMemo(() => {
    if (view === 'detailed') {
      return detailedData.map(d => ({ name: d.component_name, simulant_pct: d.value_pct }));
    }
    return groupData.map(g => {
      const entry: Record<string, unknown> = { name: g.group_name, simulant_pct: g.value_pct };
      if (lunarRef?.mineral_composition) {
        entry.lunar_pct = lunarRef.mineral_composition[g.group_name] || 0;
      }
      return entry;
    });
  }, [view, detailedData, groupData, lunarRef]);

  const tableData = useMemo(() => {
    if (view === 'detailed') {
      return detailedData.map(d => ({
        name: d.component_name,
        value: d.value_pct,
        refValue: undefined as number | undefined,
      }));
    }
    return groupData.map(g => ({
      name: g.group_name,
      value: g.value_pct,
      refValue: lunarRef?.mineral_composition?.[g.group_name],
    }));
  }, [view, detailedData, groupData, lunarRef]);

  const hasData = view === 'detailed' ? detailedData.length > 0 : groupData.length > 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity size={18} className="text-emerald-400" />
          <h3 className="text-lg font-semibold text-slate-200">Mineral Composition</h3>
        </div>
        <div className="flex items-center gap-2">
          <ToggleButtonGroup
            options={[{ label: 'Detailed', value: 'detailed' }, { label: 'Groups', value: 'groups' }]}
            value={view} onChange={(v) => setView(v as 'detailed' | 'groups')}
          />
          <ToggleButtonGroup
            options={[{ label: 'Chart', value: 'chart' }, { label: 'Table', value: 'table' }]}
            value={displayMode} onChange={(v) => setDisplayMode(v as 'chart' | 'table')}
          />
        </div>
      </div>

      {view === 'groups' && missionsWithMinerals.length > 0 && (
        <div className="mb-3">
          <select value={lunarRefMission} onChange={(e) => setLunarRefMission(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg py-1.5 px-3 text-xs text-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500/50">
            <option value="">No lunar reference comparison</option>
            {missionsWithMinerals.map(r => <option key={r.mission} value={r.mission}>{r.mission}</option>)}
          </select>
        </div>
      )}

      {!hasData ? (
        <div className="bg-slate-800/30 rounded-xl p-8 text-center border border-slate-700/30">
          <p className="text-slate-500 italic">No mineral composition data available</p>
        </div>
      ) : displayMode === 'chart' ? (
        <div className="h-[300px] w-full bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
              <XAxis type="number" hide />
              <YAxis dataKey="name" type="category" width={110} stroke="#94a3b8" fontSize={11} tick={{ fill: '#94a3b8' }} />
              <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '8px' }} />
              <Bar dataKey="simulant_pct" name={simulantName} fill="#10b981" radius={[0, 4, 4, 0]}>
                {chartData.map((_, i) => <Cell key={i} fill={i % 2 === 0 ? '#10b981' : '#059669'} />)}
              </Bar>
              {view === 'groups' && lunarRef && (
                <Bar dataKey="lunar_pct" name={lunarRefMission} fill="#fca311" radius={[0, 4, 4, 0]} />
              )}
              {view === 'groups' && lunarRef && <Legend />}
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <CompositionTable data={tableData} valueLabel="%" refLabel={lunarRefMission || undefined} />
      )}
    </div>
  );
}
