import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { ArrowRightLeft, X, FlaskConical, Activity, BarChart3, TableProperties } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../../utils/cn';
import type { Simulant, ChemicalComposition, Composition, MineralGroup, LunarReference } from '../../types';

type ViewMode = 'chart' | 'table';

interface CrossComparisonPanelProps {
  simulant: Simulant;
  chemicalCompositions: ChemicalComposition[];
  compositions: Composition[];
  mineralGroups: MineralGroup[];
  lunarRef: LunarReference;
  onClose: () => void;
}

export function CrossComparisonPanel({
  simulant, chemicalCompositions, compositions, mineralGroups, lunarRef, onClose,
}: CrossComparisonPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('table');

  const chemicalData = useMemo(() => {
    const simulantOxides = chemicalCompositions
      .filter(c => c.component_type === 'oxide' && c.component_name !== 'sum' && c.value_wt_pct > 0);
    const allNames = new Set([
      ...simulantOxides.map(c => c.component_name),
      ...Object.keys(lunarRef.chemical_composition || {}),
    ]);
    return Array.from(allNames).map(name => ({
      name,
      simulant: simulantOxides.find(c => c.component_name === name)?.value_wt_pct || 0,
      reference: lunarRef.chemical_composition?.[name] || 0,
    }))
      .filter(d => d.simulant > 0 || d.reference > 0)
      .sort((a, b) => (b.simulant + b.reference) - (a.simulant + a.reference));
  }, [chemicalCompositions, lunarRef]);

  const mineralData = useMemo(() => {
    const groups = mineralGroups.filter(g => g.value_pct > 0);
    const allNames = new Set([
      ...groups.map(g => g.group_name),
      ...Object.keys(lunarRef.mineral_composition || {}),
    ]);
    return Array.from(allNames).map(name => ({
      name,
      simulant: groups.find(g => g.group_name === name)?.value_pct || 0,
      reference: lunarRef.mineral_composition?.[name] || 0,
    }))
      .filter(d => d.simulant > 0 || d.reference > 0)
      .sort((a, b) => (b.simulant + b.reference) - (a.simulant + a.reference));
  }, [mineralGroups, lunarRef]);

  return (
    <motion.div
      initial={{ y: '100%' }} animate={{ y: 0 }} exit={{ y: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed bottom-0 left-0 right-0 h-[80vh] bg-slate-900/95 backdrop-blur-xl border-t border-slate-800 z-[1001] overflow-y-auto shadow-2xl"
    >
      <div className="p-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <ArrowRightLeft className="text-amber-400" size={28} />
            <div>
              <h2 className="text-2xl font-bold text-white">Cross-Comparison</h2>
              <p className="text-slate-400 text-sm">
                <span className="text-blue-400 font-semibold">{simulant.name}</span>
                <span className="mx-2">vs</span>
                <span className="text-amber-400 font-semibold">{lunarRef.mission} ({lunarRef.sample_id})</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex bg-slate-800 rounded-lg p-0.5 border border-slate-700">
              <button
                onClick={() => setViewMode('chart')}
                className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                  viewMode === 'chart' ? "bg-amber-500/20 text-amber-400" : "text-slate-400 hover:text-slate-200")}
              >
                <BarChart3 size={14} />Chart
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors",
                  viewMode === 'table' ? "bg-amber-500/20 text-amber-400" : "text-slate-400 hover:text-slate-200")}
              >
                <TableProperties size={14} />Table
              </button>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white">
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Metadata row */}
        <div className="flex gap-4 mb-6 text-xs text-slate-500">
          <span>Landing site: <span className="text-slate-300">{lunarRef.landing_site}</span></span>
          <span>Type: <span className="text-slate-300">{lunarRef.type}</span></span>
          {simulant.lunar_sample_reference && (
            <span>Simulant reference: <span className="text-slate-300">{simulant.lunar_sample_reference}</span></span>
          )}
        </div>

        {/* Comparison sections */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {viewMode === 'chart' ? (
            <>
              <ChartSection
                title="Chemical Composition (wt%)"
                icon={<FlaskConical className="text-blue-400" size={20} />}
                data={chemicalData}
                simulantName={simulant.name}
                refName={lunarRef.mission}
              />
              {mineralData.length > 0 && (
                <ChartSection
                  title="Mineral Composition (%)"
                  icon={<Activity className="text-emerald-400" size={20} />}
                  data={mineralData}
                  simulantName={simulant.name}
                  refName={lunarRef.mission}
                />
              )}
            </>
          ) : (
            <>
              <DeltaTable
                title="Chemical Composition (wt%)"
                icon={<FlaskConical className="text-blue-400" size={20} />}
                data={chemicalData}
                simulantName={simulant.name}
                refName={lunarRef.mission}
              />
              {mineralData.length > 0 && (
                <DeltaTable
                  title="Mineral Composition (%)"
                  icon={<Activity className="text-emerald-400" size={20} />}
                  data={mineralData}
                  simulantName={simulant.name}
                  refName={lunarRef.mission}
                />
              )}
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}

function ChartSection({ title, icon, data, simulantName, refName }: {
  title: string; icon: React.ReactNode;
  data: { name: string; simulant: number; reference: number }[];
  simulantName: string; refName: string;
}) {
  return (
    <section>
      <div className="flex items-center gap-3 mb-4">
        {icon}
        <h3 className="text-lg font-bold text-white">{title}</h3>
      </div>
      <div className="h-[400px] bg-slate-900/50 rounded-2xl p-4 border border-slate-800">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
            <XAxis type="number" stroke="#64748b" fontSize={11} />
            <YAxis dataKey="name" type="category" width={60} stroke="#64748b" fontSize={11} tick={{ fill: '#94a3b8' }} />
            <Tooltip
              formatter={(value: number, name: string) => [`${value.toFixed(2)}`, name]}
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px' }}
            />
            <Bar dataKey="simulant" name={simulantName} fill="#3b82f6" radius={[0, 4, 4, 0]} />
            <Bar dataKey="reference" name={refName} fill="#fca311" radius={[0, 4, 4, 0]} />
            <Legend />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

function DeltaTable({ title, icon, data, simulantName, refName }: {
  title: string; icon: React.ReactNode;
  data: { name: string; simulant: number; reference: number }[];
  simulantName: string; refName: string;
}) {
  return (
    <section>
      <div className="flex items-center gap-3 mb-4">
        {icon}
        <h3 className="text-lg font-bold text-white">{title}</h3>
      </div>
      <div className="bg-slate-900/50 rounded-2xl border border-slate-800 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="py-2.5 px-4 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">Component</th>
              <th className="py-2.5 px-4 text-right text-xs font-bold text-blue-400 uppercase tracking-wider truncate max-w-[120px]">{simulantName}</th>
              <th className="py-2.5 px-4 text-right text-xs font-bold text-amber-400 uppercase tracking-wider truncate max-w-[120px]">{refName}</th>
              <th className="py-2.5 px-4 text-right text-xs font-bold text-slate-500 uppercase tracking-wider">{'\u0394'}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row, i) => {
              const diff = row.simulant - row.reference;
              return (
                <tr key={row.name} className={i % 2 === 0 ? 'bg-slate-800/20' : ''}>
                  <td className="py-2 px-4 text-slate-300 font-medium">{row.name}</td>
                  <td className="py-2 px-4 text-right font-mono text-slate-200">{row.simulant > 0 ? row.simulant.toFixed(2) : '\u2014'}</td>
                  <td className="py-2 px-4 text-right font-mono text-slate-200">{row.reference > 0 ? row.reference.toFixed(2) : '\u2014'}</td>
                  <td className={cn("py-2 px-4 text-right font-mono text-xs",
                    diff > 0 ? "text-blue-400" : diff < 0 ? "text-amber-400" : "text-slate-500"
                  )}>
                    {row.simulant > 0 && row.reference > 0 ? `${diff > 0 ? '+' : ''}${diff.toFixed(2)}` : '\u2014'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {data.length === 0 && (
          <div className="flex items-center justify-center h-20 text-slate-500 text-sm">No data available</div>
        )}
      </div>
    </section>
  );
}
